import streamlit as st
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

# 1. Connect to local Ollama
provider = OpenAIProvider(base_url="http://localhost:11434/v1", api_key="ollama")
agent_model = OpenAIChatModel("llama3", provider=provider)

# 2. Multi-Agent Setup
summarizer_agent = Agent(
    model=agent_model,
    system_prompt="You are a teacher's assistant. Summarize these class notes in 3 clear bullet points."
)
tutor_agent = Agent(
    model=agent_model,
    system_prompt="You are a Socratic tutor. Do NOT give the direct answer. Guide the student to the answer by asking helpful questions based ONLY on the provided notes."
)
fact_checker_agent = Agent(
    model=agent_model,
    system_prompt="You are a strict grader. Review the Tutor's response against the Teacher's notes. If the Tutor makes up facts not in the notes, reply with 'FAIL'. If the Tutor is accurate, reply with 'PASS'."
)

# 3. UI Upgrade - Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/AMD_logo_2022.svg/2560px-AMD_logo_2022.svg.png", width=100)
    st.title("Agent 0")
    st.write("**The Multi-Agent AI Tutor**")
    st.divider()
    st.markdown("### 🛡️ The Walled Garden")
    st.write("Unlike generic AI, Agent 0 only uses the teacher's notes. Zero hallucinations. Zero cheating.")
    st.divider()
    st.markdown("### 🤖 The Agents")
    st.write("1. **Summarizer:** Processes notes.")
    st.write("2. **Socratic Tutor:** Guides the student.")
    st.write("3. **Fact Checker:** Verifies accuracy.")
    st.divider()
    st.caption("Built for the Colleague Zero Hackathon 2026.")

# 4. Main UI
st.title("🎓 Agent 0: Multi-Agent AI Tutor")
st.write("A digital colleague for teachers, students, and parents.")

tab1, tab2 = st.tabs(["👨‍🏫 Teacher Portal", "👦 Student Portal"])

with tab1:
    st.subheader("Upload Lesson Notes")
    notes = st.text_area("Paste class notes here:", height=200, placeholder="e.g., Photosynthesis is the process by which green plants...")
    if st.button("Generate Summary (Agent 1)", type="primary"):
        if notes:
            with st.spinner("Agent 1 is summarizing..."):
                result = summarizer_agent.run_sync(notes)
                st.session_state['summary'] = result.data
                st.success("Summary Generated!")
                st.info(result.data)
        else:
            st.warning("Please paste some notes first.")

with tab2:
    st.subheader("Student Tutor")
    if 'summary' in st.session_state:
        st.write("**Today's Lesson Summary:**")
        st.success(st.session_state['summary'])
        st.divider()
        
        question = st.text_input("What are you confused about?")
        if st.button("Ask Tutor (Agent 2 & 3)", type="primary"):
            if question:
                with st.spinner("Agent 2 (Tutor) is thinking..."):
                    prompt = f"Teacher Notes: {st.session_state['summary']}\n\nStudent Question: {question}"
                    tutor_response = tutor_agent.run_sync(prompt)
                    
                    with st.spinner("Agent 3 (Fact Checker) is verifying accuracy..."):
                        check_prompt = f"Notes: {st.session_state['summary']}\nTutor Response: {tutor_response.data}"
                        check_result = fact_checker_agent.run_sync(check_prompt)
                        
                    st.chat_message("assistant").write(tutor_response.data)
                    
                    if "PASS" in check_result.data.upper():
                        st.caption("✅ Agent 3 Verified: Accurate based on teacher notes.")
                    else:
                        st.caption("⚠️ Agent 3 Warning: Potential hallucination detected.")
    else:
        st.warning("⚠️ Waiting for teacher to upload notes first! Go to the Teacher Portal tab.")