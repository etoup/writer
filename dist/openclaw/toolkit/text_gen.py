#!/usr/bin/env python3
"""
LLM text generation module for Writer.

Supports multiple providers with auto-fallback via OpenAI-compatible API format.

Usage as CLI:
    python3 text_gen.py --prompt "Write an article about AI" --model deepseek-chat
    python3 text_gen.py --prompt "..." --provider openai --model gpt-4o

Usage as module:
    from text_gen import generate_text
    result = generate_text("system prompt", "user prompt")
"""

import abc
import json
import sys
from pathlib import Path

import requests
import yaml

CONFIG_PATHS = [
    Path.cwd() / "config.yaml",
    Path(__file__).parent.parent / "config.yaml",
    Path(__file__).parent / "config.yaml",
    Path.home() / ".config" / "writer" / "config.yaml",
]


def _load_config() -> dict:
    for p in CONFIG_PATHS:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


class TextProvider(abc.ABC):
    """Base class for text generation providers."""

    @abc.abstractmethod
    def generate(self, system: str, user: str, temperature: float = 0.7,
                 max_tokens: int = 8192) -> str:
        """Generate text and return the content string."""
        ...

    @property
    @abc.abstractmethod
    def provider_key(self) -> str:
        ...


class OpenAICompatibleProvider(TextProvider):
    """OpenAI-compatible API provider (works with OpenAI, DeepSeek, SiliconFlow, etc.)."""

    provider_key = "openai_compatible"

    def __init__(self, api_key: str, model: str = "gpt-4o",
                 base_url: str = "https://api.openai.com/v1", **_kw):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    def generate(self, system: str, user: str, temperature: float = 0.7,
                 max_tokens: int = 8192) -> str:
        resp = requests.post(
            f"{self._base_url}/chat/completions",
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=180,
        )
        data = resp.json()
        if resp.status_code != 200:
            raise ValueError(f"Text generation error ({resp.status_code}): "
                             f"{json.dumps(data, ensure_ascii=False)[:500]}")
        return data["choices"][0]["message"]["content"]


class DashScopeTextProvider(TextProvider):
    """Alibaba DashScope (通义千问) text generation."""

    provider_key = "dashscope_text"

    def __init__(self, api_key: str, model: str = "qwen-max",
                 base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1", **_kw):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    def generate(self, system: str, user: str, temperature: float = 0.7,
                 max_tokens: int = 8192) -> str:
        resp = requests.post(
            f"{self._base_url}/chat/completions",
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=180,
        )
        data = resp.json()
        if resp.status_code != 200:
            raise ValueError(f"DashScope text error ({resp.status_code}): "
                             f"{json.dumps(data, ensure_ascii=False)[:500]}")
        return data["choices"][0]["message"]["content"]


TEXT_PROVIDERS = {
    "openai_compatible": OpenAICompatibleProvider,
    "dashscope_text": DashScopeTextProvider,
}


def _build_text_provider_chain(config: dict) -> list[TextProvider]:
    """Build text providers from config."""
    text_cfg = config.get("text", {})
    providers_list = text_cfg.get("providers")

    if providers_list and isinstance(providers_list, list):
        chain = []
        for entry in providers_list:
            provider_name = entry.get("provider", "openai_compatible")
            api_key = entry.get("api_key")
            if not api_key:
                continue
            provider_cls = TEXT_PROVIDERS.get(provider_name, OpenAICompatibleProvider)
            kwargs = {"api_key": api_key}
            if entry.get("model"):
                kwargs["model"] = entry["model"]
            if entry.get("base_url"):
                kwargs["base_url"] = entry["base_url"]
            chain.append(provider_cls(**kwargs))
        return chain

    # Legacy single provider
    api_key = text_cfg.get("api_key")
    if not api_key:
        return []
    provider_name = text_cfg.get("provider", "openai_compatible")
    provider_cls = TEXT_PROVIDERS.get(provider_name, OpenAICompatibleProvider)
    return [provider_cls(
        api_key=api_key,
        model=text_cfg.get("model", "gpt-4o"),
        base_url=text_cfg.get("base_url", "https://api.openai.com/v1"),
    )]


def generate_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    config: dict = None,
) -> str:
    """Generate text using configured providers with auto-fallback."""
    if config is None:
        config = _load_config()

    chain = _build_text_provider_chain(config)
    if not chain:
        raise ValueError(
            "No text generation providers configured. "
            "Add text.providers to config.yaml to enable per-platform article generation."
        )

    last_error = None
    for provider in chain:
        try:
            return provider.generate(system_prompt, user_prompt, temperature, max_tokens)
        except Exception as e:
            last_error = e
            print(f"Text provider '{provider.provider_key}' failed: {e}. Trying next...", file=sys.stderr)

    raise ValueError(f"All text providers failed. Last error: {last_error}")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Generate text using LLM")
    ap.add_argument("--prompt", required=True, help="User prompt")
    ap.add_argument("--system", default="", help="System prompt (optional)")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=8192)
    args = ap.parse_args()

    try:
        config = _load_config()
        result = generate_text(args.system, args.prompt, args.temperature, args.max_tokens, config)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
