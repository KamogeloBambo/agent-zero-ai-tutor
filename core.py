"""Agent 0 core logic: prompts, settings, agent construction, verdict parsing.

No Streamlit in here, so tests and the benchmark script can import it freely.
"""
import re
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

# --- SETTINGS ---
BASE_URL = "http://localhost:11434/v1"  # Ollama. For a vLLM server use "http://localhost:8000/v1"
MODEL_NAME = "llama3.2"
API_KEY = "ollama"
MAX_TRIES = 3  # how many times Agent 2 may retry after Agent 3 rejects a reply

FALLBACK = (
    "I couldn't verify a reply against your teacher's notes, so I won't guess. "
    "Please ask your teacher about this one."
)

SUMMARIZER_PROMPT = (
    "You are a teacher's assistant. Summarize these class notes in 3 clear bullet points "
    "for a student who missed class. Only use facts that appear in the notes."
)
TUTOR_PROMPT = (
    "You are a Socratic tutor. Do NOT give the direct answer. Guide the student toward it by "
    "asking one or two helpful questions, using ONLY facts from the teacher's notes. "
    "Never add facts that are not written in the notes. "
    "If the notes do not cover the question, say so and tell the student to ask their teacher. "
    "If the student asks you to just give the answer, do not refuse vaguely and do not ask what they "
    "want to know. Give one small hint taken from the notes, then ask one simpler question that "
    "moves them a step closer."
)
CHECKER_PROMPT = (
    "You are a strict grader. You receive the teacher's notes, the student's question, and the tutor's reply. "
    "Answer FAIL if EITHER is true: "
    "(1) the reply states a specific fact that is not in the notes, or "
    "(2) the reply gives the complete direct answer instead of guiding the student. "
    "Answer PASS if the reply only uses facts from the notes and guides the student with a hint or question. "
    "Your first line must be exactly one word: PASS or FAIL. "
    "On the second line, give one short reason."
)


def out(result):
    """Works with both newer (.output) and older (.data) PydanticAI versions."""
    return result.output if hasattr(result, "output") else result.data


def parse_check(text):
    """Read Agent 3's verdict forgivingly. First PASS/FAIL word wins. Returns (passed, reason)."""
    m = re.search(r"\b(PASS|FAIL)\b", text.upper())
    if m:
        return m.group(1) == "PASS", text.strip()
    return False, text.strip()  # unclear verdict is treated as a failure (safe default)


def build_agents(base_url=BASE_URL, model_name=MODEL_NAME):
    """Create the three agents. Takes plain arguments so it works outside Streamlit."""
    provider = OpenAIProvider(base_url=base_url, api_key=API_KEY)
    model = OpenAIChatModel(model_name, provider=provider)
    return (
        Agent(model=model, system_prompt=SUMMARIZER_PROMPT),
        Agent(model=model, system_prompt=TUTOR_PROMPT),
        Agent(model=model, system_prompt=CHECKER_PROMPT),
    )