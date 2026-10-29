# Streamlit app: chat loop, request cap, feedback report ---
# AI-assisted starter code (Claude, Anthropic). Review and edit before committing.
#
# This is the only file Streamlit runs. It calls everything else:
# prompts.py -> what the models are told
# tools.py -> functions the interviewer model can call (uses retrieval.py)
# schemas.py -> the shape the feedback report must come back in
#
# Failure paths handled here: empty input, API errors (one retry), bad JSON
# (one retry, then a friendly error), the usage cap, and spinners while waiting.

import json
import time
import streamlit as st
from google import genai
from google.genai import types
from pydantic import ValidationError
from config import CHAT_MODEL, TEMPERATURE, MAX_REQUESTS_PER_SESSION
from prompts import INTERVIEWER_PROMPTS, FEEDBACK_PROMPTS, ACTIVE_VERSION
from schemas import FeedbackReport
from tools import get_question, get_rubric
from retrieval import search

st.set_page_config(page_title="PM Case Coach")
st.title("PM Case Coach")
st.caption("Practice a B2B SaaS PM interview. Questions and feedback are generated "
           "by a language model and may be wrong. This is practice, not professional advice.")

# ---- setup once per browser session ----
ss = st.session_state
if "client" not in ss:
    ss.client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    ss.messages, ss.tool_log, ss.token_log = [], [], []
    ss.requests, ss.started, ss.finished = 0, False, False


def under_cap():
    """Usage cap required by directives §3.2."""
    if ss.requests >= MAX_REQUESTS_PER_SESSION:
        st.warning("You reached the practice limit for this session. Refresh to start over.")
        return False
    ss.requests += 1
    return True


def send(text):
    """Send a message to the interviewer, retrying once if the API fails."""
    for attempt in range(2):
        try:
            resp = ss.chat.send_message(text)
            ss.token_log.append(("interviewer", resp.usage_metadata.total_token_count))
            return resp.text
        except Exception as e:
            st.caption(f"Debug: {type(e).__name__}: {e}")  # remove before submitting
            if attempt == 0:
                st.info("The model did not answer. Retrying once...")
                time.sleep(2)
    st.error("The model is not responding right now. Wait a minute and try again.")
    return None


def get_feedback(transcript):
    """Structured output: returns a FeedbackReport, or None if it never parses."""
    rubric = "\n\n".join(h["text"] for h in search(ss.client, transcript[-3000:], k=4))
    prompt = FEEDBACK_PROMPTS[ACTIVE_VERSION].replace("{rubric}", rubric)
    for attempt in range(2):
        try:
            resp = ss.client.models.generate_content(
                model=CHAT_MODEL, contents=transcript,
                config=types.GenerateContentConfig(
                    system_instruction=prompt, temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=FeedbackReport))
            ss.token_log.append(("feedback", resp.usage_metadata.total_token_count))
            report = FeedbackReport.model_validate_json(resp.text)
            report.overall_score = min(max(report.overall_score, 1), 5)
            return report
        except ValidationError:
            continue  # bad JSON: try once more
        except Exception:
            time.sleep(2)  # API error: wait and retry
    return None


# ---- sidebar: setup and controls ----
with st.sidebar:
    st.selectbox("Company type", ["B2B SaaS"], disabled=True)
    st.selectbox("Role level", ["MBA PM intern"], disabled=True)
    if st.button("Start interview", disabled=ss.started) and under_cap():
        ss.chat = ss.client.chats.create(model=CHAT_MODEL, config=types.GenerateContentConfig(
            system_instruction=INTERVIEWER_PROMPTS[ACTIVE_VERSION],
            tools=[get_question, get_rubric], temperature=TEMPERATURE))
        ss.started = True
        with st.spinner("Contacting the interviewer..."):
            reply = send("Please start the interview.")
        if reply:
            ss.messages.append(("assistant", reply))
    if st.button("End interview and get feedback", disabled=not ss.started):
        ss.finished = True
    # Preloaded example (directives §5.4): see a full report without doing an interview
    if st.button("Try a demo transcript"):
        with open("data/sample_transcript.json") as f:
            demo = json.load(f)
        ss.messages, ss.started, ss.finished = [tuple(m) for m in demo], True, True
        ss.pop("report", None)
    with st.expander("Behind the scenes: tool calls"):
        st.write(ss.tool_log)

# ---- the conversation ----
for role, text in ss.messages:
    st.chat_message(role).write(text)

if ss.started and not ss.finished:
    answer = st.chat_input("Type your answer")
    if answer is not None:
        if not answer.strip():
            st.warning("Your answer is empty. Type something to continue.")
        elif under_cap():
            ss.messages.append(("user", answer))
            with st.spinner("The interviewer is reading your answer..."):
                reply = send(answer)
            if reply:
                ss.messages.append(("assistant", reply))
                if "end of the interview" in reply.lower():
                    ss.finished = True
            st.rerun()

# ---- the feedback report ----
if ss.finished:
    if not any(role == "user" for role, _ in ss.messages):
        st.info("Answer at least one question to get feedback.")
    else:
        if "report" not in ss and under_cap():
            transcript = "\n\n".join(f"{r.upper()}: {t}" for r, t in ss.messages)
            with st.spinner("Writing your feedback report..."):
                ss.report = get_feedback(transcript)
        report = ss.get("report")
        if report is None:
            st.error("We couldn't build your report this time. Please try again in a minute.")
        else:
            st.subheader(f"Overall: {report.overall_score} / 5")
            st.markdown("**Strengths**")
            for s in report.strengths:
                st.write("- " + s)
            st.markdown("**What to work on**")
            for w in report.weaknesses:
                st.write(f"- **{w.category.replace('_', ' ')}**: {w.evidence}. Fix: {w.how_to_fix}")
            st.markdown("**Next steps**")
            for r in report.recommendations:
                st.write("- " + r)
