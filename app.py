import os
import html as _html
import streamlit as st
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

# --- SETTINGS ---
BASE_URL = "http://localhost:11434/v1"  # Ollama. For a vLLM server use "http://localhost:8000/v1"
MODEL_NAME = "llama3"
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
    "If the notes do not cover the question, say so and tell the student to ask their teacher."
)
CHECKER_PROMPT = (
    "You are a strict fact checker. You get the teacher's notes and a tutor's reply. "
    "If the reply states or implies any fact that is not supported by the notes, answer FAIL. "
    "Otherwise answer PASS. Your first line must be exactly one word: PASS or FAIL. "
    "On the second line, give one short sentence explaining why."
)

# --- ONE-TIME LIGHT THEME SETUP ---
# Writes .streamlit/config.toml in the folder you run Streamlit from, so every widget
# uses the same light palette as the custom styling below.
THEME = """[theme]
base = "light"
primaryColor = "#176d68"
backgroundColor = "#f7f8f5"
secondaryBackgroundColor = "#edf4f1"
textColor = "#172b35"
font = "sans serif"
"""
CONFIG_PATH = os.path.join(".streamlit", "config.toml")
current_theme = None
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            current_theme = f.read()
    except Exception:
        current_theme = None
theme_changed = current_theme != THEME
if theme_changed:
    os.makedirs(".streamlit", exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(THEME)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Agent 0 | AI Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

if theme_changed:
    st.info("Theme file updated. Stop the app (Ctrl+C) and run it once more to apply it fully.")

# --- SESSION STATE ---
defaults = {
    "messages": [],
    "notes": "",
    "summary": "",
    "conn": ("Ready to connect", ""),
    "teacher_notice": None,
    "student_notice": None,
    "retry_q": None,
}
for _k, _v in defaults.items():
    st.session_state.setdefault(_k, _v)

# --- STYLING ---
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {
  --ink:#172b35; --muted:#60717a; --teal:#176d68; --teal-dark:#105651; --teal-soft:#e7f3f0;
  --paper:#f7f8f5; --line:#dce5e2; --amber:#9b621b; --amber-soft:#fff4e2;
  --blue:#315f9b; --blue-soft:#edf4ff; --red:#ae4143; --red-soft:#fff0ef;
  --shadow:0 14px 40px rgba(24,54,59,.055);
}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background: var(--paper) !important; color: var(--ink); font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1120px; padding-top: 2.4rem; padding-bottom: 5rem; }

/* Sidebar */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { background: #123e43 !important; }
[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapseButton"] svg { color: #e8f5f2 !important; }
.a0-side, .a0-side div, .a0-side span, .a0-side li { color: #c9e0dc; }
.a0-side .a0-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 26px; }
.a0-side .a0-brand-mark { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 13px; background: #d7f0e8; font-size: 22px; }
.a0-side .a0-brand-name { font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 21px; letter-spacing: -.06em; color: #fff; }
.a0-side .a0-brand-sub { font-size: 11px; color: #bdd9d5; font-weight: 700; text-transform: uppercase; letter-spacing: .13em; }
.a0-side .a0-side-label { font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: .13em; color: #93bcb7; margin: 0 0 11px; }
.a0-side .a0-side-card { background: rgba(255,255,255,.075); border: 1px solid rgba(255,255,255,.11); border-radius: 16px; padding: 17px; margin-bottom: 26px; }
.a0-side .a0-side-card strong { font-size: 14px; color: #fff; }
.a0-side .a0-side-card div.a0-side-text { margin-top: 9px; font-size: 13px; }
.a0-side .a0-agents { list-style: none; padding: 0; margin: 0 0 26px; display: grid; gap: 16px; }
.a0-side .a0-agents li { display: flex; gap: 10px; font-size: 13px; }
.a0-side .a0-agent-icon { flex: 0 0 30px; height: 30px; display: grid; place-items: center; border-radius: 9px; background: rgba(255,255,255,.1); font-size: 15px; }
.a0-side .a0-agents strong { display: block; color: #fff; font-size: 13px; }
.a0-side .a0-side-foot { border-top: 1px solid rgba(255,255,255,.13); padding-top: 18px; color: #a9c8c4; font-size: 12px; }

/* Header */
.a0-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; }
.a0-eyebrow { color: var(--teal); font-weight: 800; font-size: 11px; letter-spacing: .15em; text-transform: uppercase; margin: 0 0 10px; }
.a0-h1 { font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 40px; line-height: 1.15; letter-spacing: -.045em; color: var(--ink); margin: 0 0 9px; }
.a0-h2 { font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 22px; letter-spacing: -.045em; color: var(--ink); margin: 0 0 3px; }
.a0-h3 { font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 17px; letter-spacing: -.04em; color: var(--ink); margin: 0 0 5px; }
.a0-intro { color: var(--muted); max-width: 700px; font-size: 15px; line-height: 1.55; }
.a0-conn { display: inline-flex; align-items: center; gap: 7px; flex: none; padding: 8px 11px; border: 1px solid var(--line); background: #fff; border-radius: 999px; font-size: 12px; font-weight: 700; color: var(--muted); }
.a0-dot { width: 7px; height: 7px; border-radius: 50%; background: #a8b8b3; }
.a0-conn.active .a0-dot { background: #2e9d78; }
.a0-conn.error .a0-dot { background: var(--red); }

/* Tabs */
[data-baseweb="tab-list"] { gap: 7px; margin-top: 18px; }
button[data-baseweb="tab"] { background: transparent; padding: 12px 18px 15px; border-radius: 8px 8px 0 0; }
button[data-baseweb="tab"] p { font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 15px; color: var(--muted) !important; }
button[data-baseweb="tab"][aria-selected="true"] p { color: var(--teal) !important; }
button[data-baseweb="tab"]:hover { background: #eaf1ee; }
[data-baseweb="tab-highlight"] { background-color: var(--teal) !important; height: 3px !important; }
[data-baseweb="tab-border"] { background-color: var(--line) !important; }

/* Portal header */
.a0-portal { display: flex; align-items: center; gap: 15px; margin: 8px 0 20px; }
.a0-portal-icon { width: 48px; height: 48px; flex: none; display: grid; place-items: center; border-radius: 14px; font-size: 22px; }
.a0-portal.teacher .a0-portal-icon { background: var(--amber-soft); }
.a0-portal.student .a0-portal-icon { background: var(--blue-soft); }
.a0-portal-sub { color: var(--muted); font-size: 13px; }

/* Cards */
[class*="st-key-card"] { background: #fff; border: 1px solid var(--line); border-radius: 18px; box-shadow: var(--shadow); padding: 25px; }
.st-key-card_summary { border-left: 4px solid var(--teal); }
.st-key-card_studentsummary { background: var(--blue-soft); border-color: #dce6f5; }
.a0-desc { color: var(--muted); font-size: 13px; margin: 0 0 14px; line-height: 1.5; }
.a0-help { color: var(--muted); font-size: 12px; line-height: 1.5; }
.a0-small { color: var(--muted); font-size: 12px; padding-top: 12px; }
.a0-text { white-space: pre-wrap; overflow-wrap: anywhere; font-size: 14px; line-height: 1.7; color: var(--ink); }
.st-key-card_studentsummary .a0-text { font-size: 13px; color: #244d80; }
.st-key-card_studentsummary .a0-h3 { color: #244d80; }

/* Inputs */
[data-testid="stWidgetLabel"] p { font-size: 13px; font-weight: 800; color: var(--ink); }
[data-baseweb="textarea"], [data-baseweb="base-input"], [data-baseweb="input"] { background: #fbfcfa !important; border-radius: 11px !important; border-color: #cfdad6 !important; }
[data-baseweb="textarea"] textarea, [data-baseweb="base-input"] input { background: #fbfcfa !important; color: var(--ink) !important; font-family: 'DM Sans', sans-serif; font-size: 14px; }
[data-baseweb="textarea"]:focus-within, [data-baseweb="base-input"]:focus-within { border-color: var(--teal) !important; box-shadow: 0 0 0 3px rgba(23,109,104,.14); }
[data-testid="stForm"] { border: none; padding: 0; background: transparent; }

/* Buttons */
.stButton button, [data-testid="stFormSubmitButton"] button { border-radius: 10px; font-size: 13px; min-height: 43px; padding: 11px 17px; font-family: 'DM Sans', sans-serif; transition: .2s; }
button p { font-weight: 800 !important; color: inherit !important; }
button[kind="primary"], button[kind="primaryFormSubmit"], [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] { background: var(--teal) !important; color: #fff !important; border: 1px solid transparent !important; }
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover, [data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover { background: var(--teal-dark) !important; color: #fff !important; }
button[kind="secondary"], [data-testid="stBaseButton-secondary"] { background: #fff !important; color: var(--teal) !important; border: 1px solid #c7d9d4 !important; }
button[kind="secondary"]:hover, [data-testid="stBaseButton-secondary"]:hover { background: var(--teal-soft) !important; }
button:disabled { opacity: .55; }

/* Expander + status */
[data-testid="stExpander"] { border: none; border-top: 1px solid var(--line); border-radius: 0; background: transparent; }
[data-testid="stExpander"] summary p { color: var(--teal); font-size: 13px; font-weight: 800; }
[data-testid="stStatus"] { background: #fff; border: 1px solid var(--line); border-radius: 12px; }

/* Notices */
.a0-notice { display: flex; gap: 11px; align-items: flex-start; border-radius: 12px; padding: 13px 15px; font-size: 13px; margin: 6px 0 4px; border: 1px solid; }
.a0-notice strong { display: block; }
.a0-notice-icon { flex: none; font-weight: 800; width: 18px; text-align: center; }
.a0-notice.info { background: var(--blue-soft); border-color: #d2e1f8; color: #28527f; }
.a0-notice.success { background: var(--teal-soft); border-color: #c7e4d9; color: #175d50; }
.a0-notice.warning { background: var(--amber-soft); border-color: #f0dfc1; color: #805117; }
.a0-notice.error { background: var(--red-soft); border-color: #efcecc; color: #913638; }

/* Steps */
.a0-steps { list-style: none; margin: 16px 0 0; padding: 0; display: grid; gap: 15px; }
.a0-steps li { display: flex; gap: 10px; font-size: 13px; color: var(--muted); }
.a0-stepnum { width: 24px; height: 24px; border-radius: 50%; background: var(--teal-soft); color: var(--teal); display: grid; place-items: center; flex: none; font-size: 11px; font-weight: 800; }
.a0-steps strong { display: block; color: var(--ink); }

/* Chat */
.a0-chat-head { display: flex; justify-content: space-between; gap: 15px; align-items: center; padding-bottom: 17px; border-bottom: 1px solid var(--line); }
.a0-badge { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 800; color: var(--teal); background: var(--teal-soft); padding: 6px 9px; border-radius: 999px; white-space: nowrap; }
.a0-messages { display: flex; flex-direction: column; gap: 16px; padding: 20px 0; min-height: 200px; }
.a0-msg { max-width: 88%; }
.a0-msg.user { align-self: flex-end; }
.a0-msg.assistant { align-self: flex-start; }
.a0-bubble { border-radius: 14px; padding: 13px 16px; overflow-wrap: anywhere; font-size: 14px; line-height: 1.65; }
.a0-msg.user .a0-bubble { background: var(--blue-soft); color: #203f69; border-bottom-right-radius: 4px; }
.a0-msg.assistant .a0-bubble { background: #f2f5f2; color: var(--ink); border: 1px solid var(--line); border-bottom-left-radius: 4px; }
.a0-meta { margin-top: 7px; font-size: 11px; color: var(--muted); }
.a0-empty { text-align: center; padding: 40px 12px; color: var(--muted); }
.a0-empty-icon { width: 48px; height: 48px; border-radius: 14px; background: var(--blue-soft); display: grid; place-items: center; margin: 0 auto 14px; font-size: 22px; }
.a0-empty .a0-desc { max-width: 340px; margin: 0 auto; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# --- HELPERS ---
def esc(text):
    """Escape text for safe use inside our HTML, keeping line breaks."""
    return _html.escape(str(text)).replace("\n", "<br>")


def compact(s):
    """Streamlit treats indented or blank-line HTML as code, so flatten it to one line."""
    return "".join(line.strip() for line in s.splitlines())


def md(s):
    st.markdown(compact(s), unsafe_allow_html=True)


def card(key):
    """A white rounded card. Falls back to a plain bordered box on older Streamlit versions."""
    try:
        return st.container(key=key)
    except TypeError:
        return st.container(border=True)


def out(result):
    """Works with both newer (.output) and older (.data) PydanticAI versions."""
    return result.output if hasattr(result, "output") else result.data


def parse_check(text):
    """Read Agent 3's verdict from the first line. Returns (passed, reason)."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    first = lines[0].upper().lstrip("*#> ") if lines else ""
    return first.startswith("PASS"), text.strip()


def build_agents():
    base = st.session_state.get("base_url", BASE_URL)
    name = st.session_state.get("model_name", MODEL_NAME)
    provider = OpenAIProvider(base_url=base, api_key=API_KEY)
    model = OpenAIChatModel(name, provider=provider)
    return (
        Agent(model=model, system_prompt=SUMMARIZER_PROMPT),
        Agent(model=model, system_prompt=TUTOR_PROMPT),
        Agent(model=model, system_prompt=CHECKER_PROMPT),
    )


def friendly_error(e):
    base = st.session_state.get("base_url", BASE_URL)
    return (
        f"Could not get a response from the model at {base}. "
        f"Check that the model server is running and the model name is correct. ({type(e).__name__})"
    )


def show_notice(key):
    data = st.session_state.get(key)
    if not data:
        return
    kind, title, message = data
    icon = {"success": "✓", "error": "!", "warning": "⚠", "info": "ℹ"}.get(kind, "ℹ")
    md(f"""<div class="a0-notice {kind}"><span class="a0-notice-icon">{icon}</span><div><strong>{esc(title)}</strong><span>{esc(message)}</span></div></div>""")


def portal_header(kind, icon, title, sub):
    md(f"""<div class="a0-portal {kind}"><span class="a0-portal-icon">{icon}</span><div><div class="a0-h2">{title}</div><div class="a0-portal-sub">{sub}</div></div></div>""")


def messages_html():
    msgs = st.session_state["messages"]

    def empty(icon, title, text):
        return f"""<div class="a0-empty"><div class="a0-empty-icon">{icon}</div><div class="a0-h3">{title}</div><div class="a0-desc">{text}</div></div>"""

    if not st.session_state["notes"]:
        return empty("📖", "Start with a lesson", "Please upload notes in the Teacher Portal first! Once the summary is ready, you can ask your tutor questions here.")
    if not msgs:
        return empty("💭", "Curiosity starts here", "Ask about today’s lesson. Your tutor will guide you with questions rather than giving away the answer.")
    parts = []
    for m in msgs:
        meta = f'<div class="a0-meta">{esc(m["meta"])}</div>' if m.get("meta") else ""
        parts.append(f'<div class="a0-msg {m["role"]}"><div class="a0-bubble">{esc(m["content"])}</div>{meta}</div>')
    return '<div class="a0-messages">' + "".join(parts) + "</div>"


def run_tutor(question, add_user=True):
    """Agent 2 drafts, Agent 3 checks. Only a verified reply is ever shown."""
    notes = st.session_state["notes"]
    if add_user:
        st.session_state["messages"].append({"role": "user", "content": question})
    st.session_state["retry_q"] = None
    reply, verified, feedback, attempts_used, error = "", False, "", 0, None

    with st.status("Multi-agent workflow running...", expanded=True) as status:
        try:
            _, tutor, checker = build_agents()
            for attempt in range(1, MAX_TRIES + 1):
                attempts_used = attempt
                st.write(f"🧠 Agent 2 (Tutor) is writing a Socratic reply (attempt {attempt} of {MAX_TRIES})...")
                prompt = f"Teacher notes:\n{notes}\n\nStudent question: {question}"
                if feedback:
                    prompt += (
                        f"\n\nA fact checker rejected your previous reply: {feedback}\n"
                        "Write a new reply that stays strictly within the teacher's notes."
                    )
                draft = out(tutor.run_sync(prompt))

                st.write("🕵️ Agent 3 (Fact Checker) is verifying the reply against the notes...")
                verdict = out(checker.run_sync(f"Teacher notes:\n{notes}\n\nTutor reply:\n{draft}"))
                passed, reason = parse_check(verdict)
                if passed:
                    reply, verified = draft, True
                    st.write("✅ Check passed.")
                    break
                st.write("❌ Check failed. Sending the reply back to the Tutor.")
                feedback = reason[:300]
        except Exception as e:
            error = e

        if error is not None:
            status.update(label="The workflow stopped", state="error", expanded=False)
        elif verified:
            status.update(label="Verified by Agent 3", state="complete", expanded=False)
        else:
            status.update(label="Could not verify a reply", state="error", expanded=False)

    if error is not None:
        st.session_state["conn"] = ("Connection issue", "error")
        st.session_state["student_notice"] = (
            "error", "The workflow stopped",
            friendly_error(error) + " Your question is still in the conversation. Select Retry question to try again.",
        )
        st.session_state["retry_q"] = question
    elif verified:
        st.session_state["conn"] = ("Model connected", "active")
        st.session_state["messages"].append({
            "role": "assistant", "content": reply,
            "meta": f"✓ Agent 3 verified this reply against the teacher's notes (attempt {attempts_used} of {MAX_TRIES}).",
        })
        st.session_state["student_notice"] = ("success", "Verified by Agent 3", "This reply passed the notes-based fact check.")
    else:
        st.session_state["conn"] = ("Model connected", "active")
        st.session_state["messages"].append({
            "role": "assistant", "content": FALLBACK,
            "meta": "⚠ Agent 3 rejected every attempt, so no unverified answer was shown.",
        })
        st.session_state["student_notice"] = (
            "warning", "Could not verify a reply",
            f"All {MAX_TRIES} attempts were rejected. No unverified answer was shown.",
        )
    st.rerun()


# --- SIDEBAR ---
with st.sidebar:
    md("""
    <div class="a0-side">
      <div class="a0-brand">
        <div class="a0-brand-mark">🎓</div>
        <div><div class="a0-brand-name">Agent 0</div><div class="a0-brand-sub">The multi-agent AI tutor</div></div>
      </div>
      <div class="a0-side-label">Our approach</div>
      <div class="a0-side-card">
        <strong>🛡️ The Walled Garden</strong>
        <div class="a0-side-text">Agent 0 answers only from the teacher’s notes, and every reply is checked before the student sees it.</div>
      </div>
      <div class="a0-side-label">Working together</div>
      <ol class="a0-agents">
        <li><span class="a0-agent-icon">📝</span><span><strong>Summarizer</strong>Turns notes into a clean summary.</span></li>
        <li><span class="a0-agent-icon">💬</span><span><strong>Socratic Tutor</strong>Guides the student with questions.</span></li>
        <li><span class="a0-agent-icon">🔍</span><span><strong>Fact Checker</strong>Blocks replies the notes don’t support.</span></li>
      </ol>
      <div class="a0-side-foot">Built for the Colleague Zero Hackathon 2026.</div>
    </div>
    """)

# --- HEADER ---
conn_label, conn_state = st.session_state["conn"]
md(f"""
<div class="a0-top">
  <div>
    <div class="a0-eyebrow">A better way to learn, together</div>
    <div class="a0-h1">Agent 0: The Digital Colleague</div>
    <div class="a0-intro">A multi-agent AI ecosystem that saves teachers time and helps students learn without just getting the answer.</div>
  </div>
  <div class="a0-conn {conn_state}"><span class="a0-dot"></span>{esc(conn_label)}</div>
</div>
""")

tab_teacher, tab_student = st.tabs(["📖 Teacher Portal", "✨ Student Portal"])

# --- TEACHER PORTAL ---
with tab_teacher:
    portal_header("teacher", "📝", "Prepare the lesson", "Give students a trusted starting point, grounded in your notes.")
    left, right = st.columns([2.35, 1], gap="medium")

    with left:
        with card("card_notes"):
            md("""<div class="a0-h3">1. Upload Lesson Notes</div><div class="a0-desc">Paste your class notes below. The original notes remain the source for every student reply.</div>""")
            notes_input = st.text_area(
                "Paste messy class notes here:", height=220,
                placeholder="e.g., Photosynthesis is the process...", key="notes_input",
            )
            md("""<div class="a0-help">Starting a new lesson replaces the current summary and clears the student conversation.</div>""")
            b1, b2 = st.columns([1, 1.5])
            with b1:
                generate = st.button("✨ Generate Summary", type="primary", key="generate")
            with b2:
                state_text = "Lesson ready for students" if st.session_state["notes"] else "No lesson prepared yet"
                md(f"""<div class="a0-small">{state_text}</div>""")

        if generate:
            text = notes_input.strip()
            if not text:
                st.session_state["teacher_notice"] = ("warning", "Notes needed", "Please paste some notes first.")
                st.rerun()
            summary, error = "", None
            with st.status("Agent 1 is processing your notes...", expanded=True) as status:
                st.write("📥 Reading teacher notes...")
                try:
                    summarizer, _, _ = build_agents()
                    summary = out(summarizer.run_sync(text))
                    st.write("✅ Summary generated.")
                    status.update(label="Summary complete", state="complete", expanded=False)
                except Exception as e:
                    error = e
                    status.update(label="Could not generate a summary", state="error", expanded=False)
            if error is None:
                # Keep the RAW notes for the Tutor and Fact Checker, and the summary for students.
                st.session_state["notes"] = text
                st.session_state["summary"] = summary
                st.session_state["messages"] = []
                st.session_state["retry_q"] = None
                st.session_state["student_notice"] = None
                st.session_state["conn"] = ("Model connected", "active")
                st.session_state["teacher_notice"] = ("success", "Summary complete", "Notes processed and saved to the Walled Garden for this lesson.")
            else:
                st.session_state["conn"] = ("Connection issue", "error")
                st.session_state["teacher_notice"] = (
                    "error", "Summary could not be generated",
                    friendly_error(error) + " Your current lesson has not been changed.",
                )
            st.rerun()

        show_notice("teacher_notice")

        if st.session_state["summary"]:
            with card("card_summary"):
                md(f"""<div class="a0-h3">Lesson summary</div><div class="a0-text">{esc(st.session_state["summary"])}</div>""")

    with right:
        with card("card_how"):
            md("""
            <div class="a0-h3">How it works</div>
            <div class="a0-desc">A simple workflow with a careful safety check.</div>
            <ol class="a0-steps">
              <li><span class="a0-stepnum">01</span><span><strong>Share your notes</strong>Paste the material from today’s class.</span></li>
              <li><span class="a0-stepnum">02</span><span><strong>Generate a summary</strong>Agent 1 extracts three clear points.</span></li>
              <li><span class="a0-stepnum">03</span><span><strong>Open student questions</strong>Every tutor response is checked against your original notes.</span></li>
            </ol>
            """)
        with card("card_settings"):
            md("""<div class="a0-h3">Model configuration</div><div class="a0-desc">OpenAI-compatible local model settings.</div>""")
            with st.expander("Configure connection"):
                st.text_input("API base URL", value=BASE_URL, key="base_url")
                st.text_input("Model name", value=MODEL_NAME, key="model_name")
                md("""<div class="a0-help">Defaults match Ollama. For vLLM use an endpoint such as http://localhost:8000/v1.</div>""")

# --- STUDENT PORTAL ---
with tab_student:
    portal_header("student", "💬", "Explore the lesson", "Ask questions, think it through, and discover the answer yourself.")
    left, right = st.columns([2.35, 1], gap="medium")
    has_notes = bool(st.session_state["notes"])

    with left:
        with card("card_chat"):
            md("""<div class="a0-chat-head"><div class="a0-h3">2. Ask the AI Tutor</div><span class="a0-badge">🛡️ Notes-first learning</span></div>""")
            md(messages_html())
            show_notice("student_notice")

            if st.session_state["retry_q"]:
                if st.button("↻ Retry question", key="retry"):
                    run_tutor(st.session_state["retry_q"], add_user=False)

            with st.form("chat_form", clear_on_submit=True):
                question = st.text_input(
                    "Your question", placeholder="Ask a question about the lesson...",
                    disabled=not has_notes,
                )
                asked = st.form_submit_button("➤ Ask tutor", type="primary", disabled=not has_notes)
            if asked and question.strip():
                run_tutor(question.strip())

    with right:
        with card("card_studentsummary"):
            if st.session_state["summary"]:
                md(f"""<div class="a0-h3">Today’s lesson summary</div><div class="a0-text">{esc(st.session_state["summary"])}</div>""")
            else:
                md("""<div class="a0-h3">Today’s lesson summary</div><div class="a0-desc">Your teacher’s lesson summary will appear here after notes are prepared.</div>""")