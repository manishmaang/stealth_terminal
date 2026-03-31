import json
import requests
from abc import ABC, abstractmethod
from typing import Generator


class AIBackend(ABC):
    @abstractmethod
    def stream_response(self, messages: list[dict]) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class OllamaBackend(AIBackend):
    def __init__(self, model: str = "llama3",
                 base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def name(self) -> str:
        return f"Ollama ({self.model})"

    def stream_response(self, messages: list[dict]) -> Generator[str, None, None]:
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model, "messages": messages, "stream": True},
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            if content := data.get("message", {}).get("content"):
                yield content
            if data.get("done"):
                break

    def list_models(self) -> list[str]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []


class ClaudeBackend(AIBackend):
    def __init__(self, api_key: str,
                 model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def name(self) -> str:
        return f"Claude ({self.model.split('-')[1] if '-' in self.model else self.model})"

    def stream_response(self, messages: list[dict]) -> Generator[str, None, None]:
        client = self._get_client()
        with client.messages.stream(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text


def create_backend(config: dict) -> AIBackend:
    ai_config = config["ai"]
    backend_type = ai_config["backend"]

    if backend_type == "claude":
        api_key = ai_config.get("claude_api_key", "")
        if not api_key:
            raise ValueError("Claude API key not configured. Edit ~/.config/invisible-terminal/config.toml")
        return ClaudeBackend(
            api_key=api_key,
            model=ai_config.get("claude_model", "claude-sonnet-4-20250514"),
        )
    else:
        return OllamaBackend(
            model=ai_config.get("ollama_model", "llama3"),
            base_url=ai_config.get("ollama_url", "http://localhost:11434"),
        )
