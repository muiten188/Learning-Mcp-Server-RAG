/** An MCP server and its currently available tools. */
export interface Server {
  name: string;
  status: string;
  tools: string[];
  error?: string;
}
