# Written with Claude (Anthropic) as coding assistant. Log the exchange in the GenAI appendix.
# --- Caitlin: Gemini client, JSON parsing, embeddings (change name to the real owner) ---
import json
import os
import threading
from typing import Callable, Optional
from google import genai
from google.genai import types

# The remaining models are tried in order when the selected model returns HTTP 503.
GEN_MODEL = "gemini-3.5-flash-lite"
GENERATION_MODELS = (
    GEN_MODEL,
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
)
TIMEOUT_MS = 60_000  # an API call that hangs longer than this becomes an LLMError (ported from starter-scaffold)
EMBED_MODEL = "gemini-embedding-001"


class LLMError(Exception):
    """API or key problem."""


class ParseError(Exception):
    """Model answered, but not with parseable JSON."""


_api_keys = None
_active_key_index = 0
_clients = {}
_state_lock = threading.Lock()


def _normalize_api_keys(value):
    if isinstance(value, str):
        values = value.replace("\n", ",").split(",")
    elif isinstance(value, (list, tuple)):
        values = value
    elif value is None:
        return []
    else:
        raise LLMError("GEMINI_API_KEYS must be a comma-separated string or a list.")
    keys = []
    for key in values:
        if not isinstance(key, str):
            raise LLMError("Each value in GEMINI_API_KEYS must be a string.")
        key = key.strip()
        if key and key not in keys:
            keys.append(key)
    return keys


def _get_api_keys():
    global _api_keys
    with _state_lock:
        if _api_keys is not None:
            return _api_keys

        keys = _normalize_api_keys(os.environ.get("GEMINI_API_KEYS"))
        if not keys and os.environ.get("GEMINI_API_KEY"):
            keys = _normalize_api_keys(os.environ["GEMINI_API_KEY"])
        if not keys:
            try:
                import streamlit as st
                keys = _normalize_api_keys(st.secrets.get("GEMINI_API_KEYS"))
                if not keys:
                    keys = _normalize_api_keys(st.secrets.get("GEMINI_API_KEY"))
            except Exception as e:
                message = f"Could not read Gemini API keys from Streamlit secrets: {e}"
                raise LLMError(message) from e
        if not keys:
            raise LLMError(
                "Set GEMINI_API_KEYS or GEMINI_API_KEY in the environment or Streamlit secrets."
            )
        _api_keys = keys
        return _api_keys


def _get_client(api_key):
    with _state_lock:
        if api_key not in _clients:
            try:
                _clients[api_key] = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(timeout=TIMEOUT_MS),
                )
            except Exception as e:
                raise LLMError(f"Could not create Gemini client: {e}") from e
        return _clients[api_key]


def _status_code(error):
    try:
        return int(error.code)
    except (AttributeError, TypeError, ValueError):
        return None


def _call_with_failover(
    request, models, on_model_status: Optional[Callable[[str], None]] = None
):
    global _active_key_index
    keys = _get_api_keys()
    model_index = 0
    retry_note = None
    while True:
        with _state_lock:
            if _active_key_index >= len(keys):
                raise LLMError("All configured Gemini API keys are quota-exhausted.")
            key_index = _active_key_index
        model = models[model_index]
        next_model = models[model_index + 1] if model_index + 1 < len(models) else None
        if on_model_status:
            if retry_note:
                message = retry_note
                retry_note = None
            else:
                message = f"Waiting for {model} to respond."
            if next_model:
                message += f" If it's unavailable, we'll try {next_model} next."
            message += f" An attempt can take up to {TIMEOUT_MS // 1000} seconds."
            on_model_status(message)
        try:
            result = request(_get_client(keys[key_index]), model)
        except LLMError:
            raise
        except Exception as e:
            code = _status_code(e)
            if code == 429:
                with _state_lock:
                    _active_key_index = max(_active_key_index, key_index + 1)
                    has_another_key = _active_key_index < len(keys)
                if has_another_key:
                    retry_note = (
                        f"Quota limit reached for this project (429). "
                        f"Retrying {model} with the next configured project key."
                    )
                    continue
                if on_model_status:
                    on_model_status(
                        "The project quota is exhausted, and no additional project keys are configured."
                    )
                message = f"All configured Gemini API keys are quota-exhausted: {e}"
                raise LLMError(message) from e
            if code == 503 and model_index + 1 < len(models):
                next_model = models[model_index + 1]
                retry_note = (
                    f"{model} is temporarily unavailable (503). Switching to {next_model}."
                )
                model_index += 1
                continue
            if code == 503 and on_model_status:
                on_model_status(
                    f"{model} is temporarily unavailable (503), and no fallback models remain."
                )
            raise LLMError(str(e)) from e
        if on_model_status:
            on_model_status(f"Response received from {model}.")
        return result


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


def generate_json(
    system,
    user,
    temperature=0.3,
    schema=None,
    on_model_status: Optional[Callable[[str], None]] = None,
):
    """Ask for JSON. If schema (a Pydantic model) is given, Gemini is constrained to that shape.
    `user` is the prompt text, or a conversation from run_tool_turn().
    Returns the parsed dict; the caller still validates it."""
    try:
        text = _call_with_failover(
            lambda client, model: client.models.generate_content(
                model=model,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=temperature,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            ).text,
            GENERATION_MODELS,
            on_model_status,
        )
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(str(e)) from e
    return parse_json(text)


# --- Caitlin: tool turn of the report conversation (written with Claude Code as coding assistant) ---
MAX_TOOL_CALLS = 4  # most tool calls we will run for one report


def run_tool_turn(
    system,
    user,
    tools,
    temperature=0.3,
    on_model_status: Optional[Callable[[str], None]] = None,
):
    """CAPABILITY: tool calling. Turn 1 of the report conversation.
    The model reads the task and DECIDES whether to call any of `tools` (plain Python functions).
    It is not forced to: no call at all is a normal outcome. Our code runs each call the model asks
    for and puts the result back into the conversation as the tool's reply.
    Returns the conversation so far; pass it to generate_json() as `user` for turn 2.
    Uses the same model and API key failover as generate_json()."""
    by_name = {t.__name__: t for t in tools}
    task = types.Content(role="user", parts=[types.Part.from_text(text=user)])
    try:
        resp = _call_with_failover(
            lambda client, model: client.models.generate_content(
                model=model,
                contents=[task],
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=temperature,
                    tools=tools,  # offered, not forced (default mode lets the model choose)
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),  # we run the calls
                ),
            ),
            GENERATION_MODELS,
            on_model_status,
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
        return _call_with_failover(
            lambda client, model: [
                e.values
                for e in client.models.embed_content(model=model, contents=texts).embeddings
            ],
            (EMBED_MODEL,),
        )
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(str(e)) from e
