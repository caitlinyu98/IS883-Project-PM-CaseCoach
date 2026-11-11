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
    `user` is the prompt text, or a conversation from run_tool_turn().
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


# --- Caitlin: tool turn of the report conversation (written with Claude Code as coding assistant) ---
MAX_TOOL_CALLS = 4  # most tool calls we will run for one report


def run_tool_turn(system, user, tools, temperature=0.3):
    """CAPABILITY: tool calling. Turn 1 of the report conversation.
    The model reads the task and DECIDES whether to call any of `tools` (plain Python functions).
    It is not forced to: no call at all is a normal outcome. Our code runs each call the model asks
    for and puts the result back into the conversation as the tool's reply.
    Returns the conversation so far; pass it to generate_json() as `user` for turn 2."""
    by_name = {t.__name__: t for t in tools}
    task = types.Content(role="user", parts=[types.Part.from_text(text=user)])
    try:
        resp = _get_client().models.generate_content(
            model=GEN_MODEL,
            contents=[task],
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                tools=tools,  # offered, not forced (default mode lets the model choose)
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),  # we run the calls
            ),
        )
        calls = resp.function_calls or []
        model_turn = resp.candidates[0].content if calls else None
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(str(e)) from e
    if not calls:
        return [task]  # the model chose not to use a tool

    replies = []
    for n, call in enumerate(calls):
        fn = by_name.get(call.name)
        if fn is None:
            result = {"error": f"unknown tool: {call.name}"}
        elif n >= MAX_TOOL_CALLS:
            result = {"error": "lookup limit reached"}
        else:
            try:
                result = fn(**dict(call.args or {}))
            except Exception as e:  # a bad argument is reported back to the model, not shown to the user
                result = {"error": str(e)}
        replies.append(types.Part.from_function_response(name=call.name, response=result))
    # the model's request, then the tool's reply: both stay in the conversation for turn 2
    return [task, model_turn, types.Content(role="user", parts=replies)]


def embed(texts):
    try:
        resp = _get_client().models.embed_content(model=EMBED_MODEL, contents=texts)
        return [e.values for e in resp.embeddings]
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(str(e)) from e
