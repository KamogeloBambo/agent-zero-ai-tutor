# 🎓 Agent 0: The Multi-Agent AI Tutor

**Colleague Zero Hackathon 2026 Submission**

## 💡 The Problem: The Education Gap & AI Cheating
Right now, education is facing a crisis. 
1. **Teachers are overwhelmed** and cannot provide 1-on-1 tutoring to every student.
2. **Parents are exhausted** after long shifts and lack the energy (or subject knowledge) to help with homework.
3. **Students are using generic AI (like ChatGPT) to cheat.** These tools give direct answers from the open internet, ignoring the school's curriculum, marking standard, and scope.

## 🛡️ The Solution: A "Walled Garden" Digital Colleague
**Agent 0** is a privacy-first, multi-agent AI tutor that acts as a digital colleague for the entire education ecosystem. 

Instead of using the open internet, Agent 0 operates in a **Walled Garden**. It uses **only the teacher's specific lesson notes** as the absolute source of truth. This eliminates cheating and ensures every answer aligns perfectly with the school's marking standard. 

### 🤖 The 3-Agent Workflow (How it works)
Agent 0 uses a sequential multi-agent workflow built with **PydanticAI**:
1. **Agent 1 (The Summarizer):** The teacher pastes their messy class notes. This agent processes them into a clean, 3-bullet study guide for absent students or parents.
2. **Agent 2 (The Socratic Tutor):** When a student asks a question, this agent **refuses to give the direct answer**. It uses the Socratic method, asking guiding questions to force the student to think and learn.
3. **Agent 3 (The Fact Checker):** This is our self-correction mechanism. Before the student sees the Tutor's answer, Agent 3 grades it against the Teacher's notes. If Agent 2 hallucinates or goes out of scope, Agent 3 flags it.

## 🛠️ Tech Stack
- **Frontend:** Streamlit (for a fast, clean UI)
- **Agent Orchestration:** PydanticAI (ReAct paradigm)
- **LLM Inference:** Ollama running Llama 3 locally (100% private, zero cloud fees)
- **Enterprise Ready:** The architecture uses the OpenAI-compatible standard, meaning it can easily be swapped to run on **vLLM with AMD Instinct GPUs** for high-performance school data centers.

## 🚀 How to Run Locally
1. Clone this repository.
2. Install dependencies: `pip install streamlit pydantic-ai-slim openai`
3. Ensure Ollama is running in the background: `ollama run llama3`
4. Start the app: `python -m streamlit run app.py`
