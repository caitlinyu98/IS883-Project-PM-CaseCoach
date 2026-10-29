# | central settings for the whole app ---
# AI-assisted starter code (Claude, Anthropic). Review and edit before committing.
#
# Every setting the app uses lives here, so a change only happens in one place.
# Copy the exact model names your Session 3 class notebook uses.

CHAT_MODEL = "gemini-3.5-flash-lite"  # free tier friendly; was gemini-3.8-flash (20 requests/day)
EMBED_MODEL = "gemini-embedding-001"   # replace with the class embedding model if different

MAX_REQUESTS_PER_SESSION = 30   # usage cap required by directives §3.2
NUM_QUESTIONS = 4               # main questions per interview
MAX_FOLLOWUPS = 3               # adaptive follow-ups per interview
TEMPERATURE = 0.4               # interviewer creativity (feedback uses 0.2)
