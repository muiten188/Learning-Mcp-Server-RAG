"""
client.py — Chat host: connects the user, a local LLM (Ollama), and the MCP server.

Run:  python client.py              (verbose debug output)
      python client.py --quiet      (hide debug lines)

Architecture overview:
  ┌──────┐   stdio    ┌────────────┐   HTTP     ┌────────┐
  │Client│◄──────────►│ MCP Server │            │ Ollama │
  │ host │            │ (server.py)│            │ LLM    │
  └──┬───┘            └────────────┘            └────────┘
     │                                               ▲
     │   messages + tool schemas (Ollama Python SDK)  │
     └───────────────────────────────────────────────┘

Flow per user message:
  1. Retrieve RAG context for the user's query.
  2. Send conversation + tool definitions to the LLM.
  3. If the LLM returns a tool call → execute it via MCP → feed result back → repeat (max 5 times).
  4. Print the final natural-language answer.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import ollama as ollama_pkg

# --- MCP SDK v2 client imports ---
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Our simple RAG module (same directory).
from rag import load_documents, build_context_block

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL = "llama3.1"  # Ollama model name — must support tool calling
MAX_TOOL_ROUNDS = 5  # Safety cap to prevent infinite tool-call loops
SERVER_SCRIPT = Path(__file__).parent / "server.py"

# Set to True via --quiet flag to hide debug output.
QUIET = False

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def debug(tag: str, msg: str) -> None:
    """Print a coloured debug line unless --quiet is set."""
    if not QUIET:
        print(f"  \033[90m[{tag}]\033[0m {msg}")


def mcp_tools_to_ollama(mcp_tools) -> list[dict]:
    """
    Convert MCP tool schemas into the format Ollama's chat API expects.

    MCP tools have:  name, description, inputSchema (JSON Schema)
    Ollama wants:    type="function", function={name, description, parameters}
    """
    ollama_tools = []
    for t in mcp_tools:
        ollama_tools.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.input_schema,  # already a JSON Schema dict
                },
            }
        )
    return ollama_tools


# ---------------------------------------------------------------------------
# Main chat loop
# ---------------------------------------------------------------------------


async def chat_loop(session: ClientSession) -> None:
    """
    Interactive chat loop.

    `session` is an initialised MCP ClientSession connected to server.py.
    """

    # 1. Discover tools from the MCP server so the LLM knows what's available.
    tools_result = await session.list_tools()
    mcp_tools = tools_result.tools
    ollama_tools = mcp_tools_to_ollama(mcp_tools)
    debug(
        "MCP",
        f"Connected — {len(mcp_tools)} tools available: "
        + ", ".join(t.name for t in mcp_tools),
    )

    # 2. Load RAG documents once at startup.
    docs = load_documents()
    debug("RAG", f"Loaded {len(docs)} documents: {list(docs.keys())}")

    # 3. Conversation history (list of {role, content} dicts).
    messages: list[dict] = []

    print("\n🤖 MCP Learning Chat  (type 'quit' to exit)\n")

    while True:
        # --- Get user input ---
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not user_input or user_input.lower() in ("quit", "exit"):
            print("Bye!")
            break

        # --- Build the system prompt with RAG context ---
        context_block = build_context_block(user_input, docs)
        system_prompt = (
            "You are a helpful assistant. You have access to tools for file "
            "management, weather lookups, and crawling web pages.\n"
            "Rules for tool usage:\n"
            "- If the user asks about an entity, company, or topic and the retrieved context "
            "contains a website link or URL (e.g. https://...), use the `crawl_webpage` tool "
            "with that URL to gather detailed information before answering.\n"
            "- Use other tools when the user's request matches them.\n"
            "- Otherwise, answer directly from your knowledge or provided context.\n"
        )
        if context_block:
            system_prompt += "\n" + context_block + "\n"
            debug("RAG", "Injected context into system prompt")

        # Add the user message to history.
        messages.append({"role": "user", "content": user_input})

        # --- Tool-call loop (up to MAX_TOOL_ROUNDS) ---
        for round_num in range(1, MAX_TOOL_ROUNDS + 1):
            debug("LLM", f"Calling Ollama ({MODEL}), round {round_num}...")

            # Call the LLM.
            response = ollama_pkg.chat(
                model=MODEL,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                tools=ollama_tools,
            )

            assistant_msg = response.message

            # Did the LLM request one or more tool calls?
            if assistant_msg.tool_calls:
                # Append the assistant message (with tool_calls) to history.
                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_msg.content or "",
                        "tool_calls": [
                            {
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                }
                            }
                            for tc in assistant_msg.tool_calls
                        ],
                    }
                )

                # Execute each tool call through MCP.
                for tc in assistant_msg.tool_calls:
                    tool_name = tc.function.name
                    tool_args = tc.function.arguments  # dict
                    debug("LLM", f"Chose tool: {tool_name}({json.dumps(tool_args)})")

                    # Call the tool on the MCP server.
                    result = await session.call_tool(tool_name, tool_args)
                    # result.content is a list of content blocks; grab the text.
                    tool_output = (
                        result.content[0].text if result.content else "(no output)"
                    )
                    debug("MCP", f"Result: {tool_output}")

                    # Feed the tool result back to the LLM as a "tool" message.
                    messages.append(
                        {
                            "role": "tool",
                            "content": tool_output,
                        }
                    )

                # Continue the loop so the LLM can process the tool results.
                continue

            else:
                # No tool call — the LLM produced a final answer.
                answer = assistant_msg.content
                messages.append({"role": "assistant", "content": answer})
                print(f"\nAssistant: {answer}\n")
                break
        else:
            # Exhausted MAX_TOOL_ROUNDS without a final answer.
            print("\n⚠️  Hit the tool-call loop limit. The model may be stuck.\n")


# ---------------------------------------------------------------------------
# Entry point — launch the MCP server subprocess and start chatting.
# ---------------------------------------------------------------------------


async def main() -> None:
    """Set up the MCP connection and run the chat loop."""

    # Define how to launch the MCP server as a subprocess.
    server_params = StdioServerParameters(
        command=sys.executable,  # same Python interpreter we're running in
        args=[str(SERVER_SCRIPT)],
    )

    debug("MCP", f"Launching server: {sys.executable} {SERVER_SCRIPT}")

    # stdio_client launches the subprocess and gives us (read, write) streams.
    async with stdio_client(server_params) as (read_stream, write_stream):
        # ClientSession wraps those streams in the MCP protocol.
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the MCP session (capability negotiation).
            await session.initialize()
            debug("MCP", "Session initialised ✓")

            # Run the interactive chat loop.
            await chat_loop(session)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Learning Chat Host")
    parser.add_argument("--quiet", "-q", action="store_true", help="Hide debug output")
    args = parser.parse_args()
    QUIET = args.quiet

    asyncio.run(main())
