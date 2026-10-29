# Written with Claude (Anthropic) as coding assistant. Log the exchange in the GenAI appendix.
# --- Caitlin: Gemini client, JSON parsing, embeddings (change name to the real owner) ---
import os
import json
from google import genai
from google.genai import types

# Verify in Google AI Studio which models your free tier allows, then edit these two lines.
# flash lite: much higher free tier quota than gemini-3.8-flash (about 20 requests a day). Demo model still to decide.
GEN_MODEL = "gemini-3.5-flash-lite"
TIMEOUT_MS = 60_000  # an API call that hangs longer than this becomes an LLMError (ported from starter-scaffold)
EMBED_MODEL = "gemini-embedding-001"


class LLMError(Exception):
    """API or key problem."""


class ParseError(Exception):
    """Model answered, but not with parseable JSON."""


_client = None


def _get_client():
    global _client
    if _client is None:
        try:
            key = os.environ.get("GEMINI_API_KEY")  # used by the eval script locally
            if not key:
                import streamlit as st
                key = st.secrets["GEMINI_API_KEY"]  # used on Streamlit Cloud (Secrets box)
            _client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=TIMEOUT_MS))
        except Exception as e:
            raise LLMError(f"Could not create Gemini client: {e}") from e
    return _client


def parse_json(text):
    if not text:
        raise ParseError("empty response")
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    try:
        return json.loads(t.strip())
    except json.JSONDecodeError as e:
        raise ParseError(str(e)) from e


def generate_json(system, user, temperature=0.3, schema=None):
    """Ask for JSON. If schema (a Pydantic model) is given, Gemini is constrained to that shape.
    Returns the parsed dict; the caller still validates it."""
    try:
        resp = _get_client().models.generate_content(
            model=GEN_MODEL,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        text = resp.text
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(str(e)) from e
    return parse_json(text)


def embed(texts):
    try:
        resp = _get_client().models.embed_content(model=EMBED_MODEL, contents=texts)
        return [e.values for e in resp.embeddings]
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(str(e)) from e
