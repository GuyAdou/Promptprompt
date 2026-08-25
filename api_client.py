import mimetypes
# Forcefully patch to bypass Windows registry initialization issue causing hangs
mimetypes.MimeTypes.read_windows_registry = lambda self, strict=True: None

import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()

# Maps each supported provider name to the .env variable that holds its key.
PROVIDER_ENV_KEYS = {
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "gpt": "OPENAI_API_KEY",
}

# Human-readable labels for the CLI provider picker.
PROVIDER_LABELS = {
    "groq": "Groq (fast & free)",
    "gemini": "Google Gemini",
    "claude": "Anthropic Claude",
    "gpt": "OpenAI GPT",
}


class BaseConnector(ABC):
    """
    Common interface every provider connector implements. optimizer.py only
    ever talks to this interface, so it doesn't need to know (or change)
    which provider is actually backing a session.
    """

    @abstractmethod
    def send_message(self, message: str, history: list | None = None) -> dict:
        """
        Send `message` to the model, preceded by `history` (a list of
        {"role": "user"|"assistant", "content": str} dicts, oldest first).

        Returns: {"content": str}
        """
        raise NotImplementedError


class GroqConnector(BaseConnector):
    """Groq. Default model is fast/free and good enough for prompt drafting."""

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b"):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = model

    def send_message(self, message, history=None):
        messages = list(history or []) + [{"role": "user", "content": message}]
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
            )
            return {"content": response.choices[0].message.content}
        except Exception as e:
            return {"content": f"Groq API Error: {str(e)}"}


class GeminiConnector(BaseConnector):
    """Google Gemini. Override the model via the GEMINI_MODEL env var."""

    def __init__(self, api_key: str, model: str | None = None):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.client = genai.GenerativeModel(self.model_name)

    def send_message(self, message, history=None):
        # Gemini's chat history uses role "model" instead of "assistant" and
        # wraps text in a "parts" list.
        gemini_history = [
            {
                "role": "model" if turn.get("role") == "assistant" else "user",
                "parts": [turn.get("content", "")],
            }
            for turn in (history or [])
        ]
        try:
            chat = self.client.start_chat(history=gemini_history)
            response = chat.send_message(message)
            return {"content": response.text}
        except Exception as e:
            return {"content": f"Gemini API Error: {str(e)}"}


class ClaudeConnector(BaseConnector):
    """
    Anthropic Claude. Defaults to claude-opus-5. Override via the
    ANTHROPIC_MODEL env var (e.g. claude-sonnet-5 for a cheaper/faster
    option on high-volume use). See https://docs.claude.com for current
    model IDs and pricing.
    """

    def __init__(self, api_key: str, model: str | None = None):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-opus-5")

    def send_message(self, message, history=None):
        import anthropic
        messages = list(history or []) + [{"role": "user", "content": message}]
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=messages,
            )
            text = next((b.text for b in response.content if b.type == "text"), "")
            return {"content": text}
        except anthropic.APIStatusError as e:
            return {"content": f"Claude API Error ({e.status_code}): {e.message}"}
        except Exception as e:
            return {"content": f"Claude API Error: {str(e)}"}


class OpenAIConnector(BaseConnector):
    """OpenAI (ChatGPT). Override the model via the OPENAI_MODEL env var."""

    def __init__(self, api_key: str, model: str | None = None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5")

    def send_message(self, message, history=None):
        messages = list(history or []) + [{"role": "user", "content": message}]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return {"content": response.choices[0].message.content}
        except Exception as e:
            return {"content": f"OpenAI API Error: {str(e)}"}


_CONNECTOR_CLASSES = {
    "groq": GroqConnector,
    "gemini": GeminiConnector,
    "claude": ClaudeConnector,
    "gpt": OpenAIConnector,
}


def available_providers() -> list:
    """
    Return provider names ("groq"/"gemini"/"claude"/"gpt") that have an API
    key set in the environment, in a fixed, stable order.
    """
    return [name for name, env_var in PROVIDER_ENV_KEYS.items() if os.getenv(env_var)]


def get_connector(provider: str) -> BaseConnector:
    """
    Instantiate the connector for `provider`.

    Raises:
        ValueError: unknown provider, or its API key isn't set.
        ImportError: the provider's SDK package isn't installed.
    """
    if provider not in PROVIDER_ENV_KEYS:
        raise ValueError(f"Unknown provider: {provider!r}")

    env_var = PROVIDER_ENV_KEYS[provider]
    api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(f"{env_var} is not set for provider {provider!r}")

    connector_cls = _CONNECTOR_CLASSES[provider]
    try:
        return connector_cls(api_key)
    except ImportError as e:
        raise ImportError(
            f"Provider '{provider}' needs an extra package that isn't "
            f"installed ({e}). See requirements-providers.txt / README."
        ) from e


if __name__ == "__main__":
    found = available_providers()
    print("Configured providers:", found or "(none)")
    if found:
        connector = get_connector(found[0])
        print(f"\n--- Testing {found[0]} ---")
        print(connector.send_message("Hello! Why are you so fast?")["content"])
