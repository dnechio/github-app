from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.models.groq import Groq


def resolve_model(provider: str, model_id: str, **kwargs):
    """
    Maps (provider, model_id) to the corresponding Agno model instance.
    Extra kwargs (temperature, max_tokens) are forwarded when supported.
    """
    match provider:
        case "anthropic":
            return Claude(id=model_id, **kwargs)
        case "openai":
            return OpenAIChat(id=model_id, **kwargs)
        case "google":
            return Gemini(id=model_id, **kwargs)
        case "groq":
            return Groq(id=model_id, **kwargs)
        case _:
            raise ValueError(f"Unknown provider: {provider!r}")


# Defaults per use-case
ROUTER_MODEL = lambda: Gemini(id="gemini-2.0-flash")
SUMMARIZER_MODEL = lambda: OpenAIChat(id="gpt-4o-mini")
