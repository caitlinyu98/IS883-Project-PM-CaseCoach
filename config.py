# | central settings for the whole app ---
# AI-assisted starter code (Claude, Anthropic). Review and edit before committing.
#
# Every setting the app uses lives here, so a change only happens in one place.
# Copy the exact model names your Session 3 class notebook uses.

CHAT_MODEL = "gemini-2.5-flash"        # replace with the class model if different
EMBED_MODEL = "gemini-embedding-001"   # replace with the class embedding model if different

MAX_REQUESTS_PER_SESSION = 30   # usage cap required by directives §3.2
NUM_QUESTIONS = 4               # main questions per interview
MAX_FOLLOWUPS = 3               # adaptive follow-ups per interview
TEMPERATURE = 0.4               # interviewer creativity (feedback uses 0.2)
