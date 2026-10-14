import json

import httpx

from app.core.config import get_settings


class Ollama:
    def __init__(self):
        self.base_url = get_settings().ollama_base_url.rstrip("/")

    async def chat(
        self, model: str, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "tools": tools or [],
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["message"]

    async def stream(self, model: str, messages: list[dict]):
        async with httpx.AsyncClient(timeout=180) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={"model": model, "messages": messages, "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        item = json.loads(line)
                        if item.get("error"):
                            raise RuntimeError(item["error"])
                        yield item.get("message", {}).get("content", "")

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={"model": get_settings().embedding_model, "input": text},
            )
            response.raise_for_status()
            return response.json()["embeddings"][0]

    async def models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return [item["name"] for item in response.json().get("models", [])]
