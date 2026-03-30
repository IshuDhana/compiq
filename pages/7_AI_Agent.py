"""
Page 7: AI Compensation Agent
Powered by Claude claude-sonnet-4-6 with tool_use — asks real questions, gets real answers from data.
"""

import streamlit as st
import sys, os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.generate_data import load_or_generate
from utils.compensation import enrich_with_market
from modules.ai_agent import CompensationAgent

st.set_page_config(page_title="AI Agent | CompIQ", layout="wide")

@st.cache_data
def get_data():
    emp, mkt, sti = load_or_generate()
    return enrich_with_market(emp, mkt), mkt, sti

df, market, sti = get_data()

st.title("AI Compensation Agent")
st.caption("Powered by GPT-4o — ask anything about your compensation data")
st.divider()

# ── API Key Check ──────────────────────────────────────────────────────────────
api_key = os.environ.get("OPENAI_API_KEY", "")
if not api_key:
    st.warning("Please set your OPENAI_API_KEY in the `.env` file to use the AI agent.")
    st.code("OPENAI_API_KEY=your_key_here", language="bash")
    st.stop()

# ── Example Prompts ────────────────────────────────────────────────────────────
st.subheader("Try these questions:")
examples = [
    "What is the gender pay gap in the Engineering department?",
    "Which employees in Germany are below market P25?",
    "How much will a 4% salary budget cost in the US?",
    "Recommend a salary for a Grade 5 Manager in the UK",
    "What is the overall gender pay gap across all countries?",
    "Show me the STI payout summary by department",
    "Which departments have the highest retention risk?",
    "Compare compa-ratios across all departments",
]

cols = st.columns(4)
clicked_prompt = None
for i, example in enumerate(examples):
    if cols[i % 4].button(example, use_container_width=True, key=f"ex_{i}"):
        clicked_prompt = example

st.divider()

# ── Chat Interface ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "raw_messages" not in st.session_state:
    st.session_state.raw_messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle example button click or user input
prompt = clicked_prompt or st.chat_input("Ask about salaries, pay gaps, STI, promotions...")

if prompt:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build raw message for API
    st.session_state.raw_messages.append({"role": "user", "content": prompt})

    # Call agent
    with st.chat_message("assistant"):
        with st.spinner("Analysing compensation data..."):
            try:
                agent = CompensationAgent(df, market, sti)
                response_text, updated_raw = agent.chat(st.session_state.raw_messages)
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                # Update raw messages (keeping tool use history for context)
                st.session_state.raw_messages = [
                    m for m in updated_raw
                    if isinstance(m.get("content"), str)
                ]
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Clear button
if st.session_state.messages:
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.raw_messages = []
        st.rerun()
