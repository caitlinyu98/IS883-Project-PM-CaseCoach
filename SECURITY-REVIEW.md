# Security review: model request limit

**Reviewed:** 2026-11-10  
**Scope:** Impact of resetting the per-session Gemini request counter when a user selects “Start over.”

| # | Severity | File | Lines | Finding | Confidence |
|---|----------|------|-------|---------|------------|
| 1 | 🟡 MEDIUM | `app.py` | 32-52 | The 12-call cap is held in Streamlit session state, not tied to a durable user identity. A new session can receive a fresh allowance. Resetting the counter on “Start over” would make repeated in-session bypass straightforward and could exhaust the app's shared Gemini quota. This is resource/quota abuse, not classic brute force. | 8/10 |

## Current behavior

The current implementation does **not** reset the request count on “Start over”: `requests` is initialized outside `INTERVIEW_DEFAULTS`, and `reset_interview()` only resets keys in `INTERVIEW_DEFAULTS`. The limit applies within a Streamlit session, so it is a usage guard, not a robust abuse-prevention boundary.

## Recommendation

Do not reset the counter on “Start over” unless the cap is replaced or supplemented by a server-side quota that persists across interview restarts. For stronger protection, enforce shared quotas using an authenticated user identity and a time window, and configure provider-side project limits/alerts. A per-session counter alone cannot prevent users from obtaining a new session and consuming another allowance.
