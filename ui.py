# Visual layer for app.py: theme injection, hero header, progress bar, and report cards.
# Styles live in assets/theme.css. Written with Claude Code as coding assistant.
import os
import streamlit as st

CSS_PATH = os.path.join(os.path.dirname(__file__), "assets", "theme.css")


def inject_theme():
    with open(CSS_PATH, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def hero(title, subtitle):
    st.markdown(
        "<div class='cc-hero'>"
        "<div class='cc-eyebrow'><span class='cc-dot'></span>AI interview simulator · B2B SaaS</div>"
        f"<div class='cc-title'>{title}</div>"
        f"<div class='cc-sub'>{subtitle}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def welcome():
    steps = [
        ("01", "Answer", "Four B2B product case questions, one at a time."),
        ("02", "Go deeper", "An adaptive follow up probes the biggest gap in each answer."),
        ("03", "Get a feedback report", "A report with your score, strengths, weaknesses, and tips to improve."),
    ]
    cards = "".join(
        f"<div class='cc-step'><div class='k'>{k}</div><div class='t'>{t}</div><div class='d'>{d}</div></div>"
        for k, t, d in steps
    )
    st.markdown(
        f"<div class='cc-welcome'><div class='cc-eyebrow'>How it works</div>"
        f"<div class='cc-steps'>{cards}</div>"
        "<div class='cc-hint'>Click <b>Start interview</b> in the sidebar to start.</div></div>",
        unsafe_allow_html=True,
    )


# state -> (fill width %, show "Q<n>", status label)
_SEG = {
    "done": (100, False, "✓ Done"),
    "followup": (0, True, "Follow up"),
    "active": (0, True, ""),
    "pending": (0, True, ""),
    "skipped": (0, False, "Skipped"),
}


def progress_states(num_questions, q_idx, phase, answered):
    """One state per question. `answered` is how many main questions are in the transcript."""
    states = []
    for i in range(num_questions):
        if phase == "ready":
            states.append("done" if i < answered else "skipped")
        elif i < q_idx:
            states.append("done")
        elif i == q_idx:
            states.append("followup" if phase == "followup" else "active")
        else:
            states.append("pending")
    return states


def progress_bar(states):
    segs = ""
    for i, s in enumerate(states):
        width, show_num, label = _SEG[s]
        num = f"<span class='n'>Q{i + 1}</span>" if show_num else ""
        status = f"<span class='st'>{label}</span>" if label else ""
        segs += (
            f"<div class='cc-seg {s}'>"
            f"<div class='cc-track'><div class='cc-fill' style='width:{width}%'></div></div>"
            f"<div class='cc-lbl'>{num}{status}</div>"
            "</div>"
        )
    with st.container(key="cc_progress"):
        st.markdown(
            "<div class='cc-progress'>"
            "<div class='cc-progress-head'><span>Interview progress</span></div>"
            f"<div class='cc-segs' style='grid-template-columns:repeat({len(states)},1fr)'>{segs}</div>"
            "</div>",
            unsafe_allow_html=True,
        )


def usage_meter(used, cap):
    pct = min(100, round(100 * used / cap)) if cap else 0
    st.markdown(
        "<div class='cc-meter'>"
        f"<div class='cc-lbl'><span>Model calls used this session</span><span class='n'>{used} of {cap}</span></div>"
        f"<div class='cc-track'><div class='cc-fill' style='width:{pct}%'></div></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def score_ring(score):
    color, verdict = (
        ("#f87171", "Needs work") if score <= 4
        else ("#fbbf24", "Getting there") if score <= 6
        else ("#34d399", "Strong")
    )
    pct = max(0, min(100, score * 10))
    st.markdown(
        "<div class='cc-score'>"
        f"<div class='cc-ring' style='background:conic-gradient({color} {pct}%, rgba(148,163,184,.16) 0);"
        f"box-shadow:0 0 26px {color}55'><span>{score}<small>/10</small></span></div>"
        f"<div><div class='cc-eyebrow'>Overall score</div>"
        f"<div class='cc-verdict' style='color:{color}'>{verdict}</div></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def card(title, items_html, color, bg, full=False):
    body = "".join(f"<li>{i}</li>" for i in items_html) or "<li>None flagged.</li>"
    return (
        f"<div class='cc-card{' full' if full else ''}' style='--c:{color};--bg:{bg}'>"
        f"<div class='cc-card-title'>{title}</div><ul>{body}</ul></div>"
    )
