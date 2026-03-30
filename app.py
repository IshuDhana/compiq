"""
CompIQ — AI Compensation Intelligence Platform
Main entry point for Streamlit multi-page app.
"""

import streamlit as st
from dotenv import load_dotenv
import sys, os

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

# Pre-generate data on first launch
from data.generate_data import load_or_generate
load_or_generate()

st.set_page_config(
    page_title="CompIQ | Compensation Intelligence",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Sidebar Branding ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💼 CompIQ")
    st.markdown("**Compensation Intelligence Platform**")
    st.caption("Sasol International Chemicals")
    st.divider()
    st.markdown("""
**Navigate using the pages above:**

1. 📊 Dashboard
2. 📈 Market Benchmarking
3. ⚖️ Gender Pay Gap
4. 💰 Salary Increase Simulator
5. 🚀 Promotion Calculator
6. 🎯 STI Tool
7. 🤖 AI Agent
    """)
    st.divider()
    st.caption("Built with GPT-4o + Streamlit")
    st.caption("Powered by OpenAI")

# ── Home Page ─────────────────────────────────────────────────────────────────
st.title("CompIQ — Compensation Intelligence Platform")
st.subheader("AI-powered rewards analytics for HR professionals")
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📊 Market Benchmarking")
    st.markdown("""
- Compare internal salaries vs P25/P50/P75/P90
- Flag retention risk (below market)
- Filter by country, department, grade
- Export to Excel
    """)

with col2:
    st.markdown("### ⚖️ Pay Equity")
    st.markdown("""
- Gender pay gap analysis (mean & median)
- Statistical significance testing
- Department, grade, country breakdown
- Auto-generate executive report
    """)

with col3:
    st.markdown("### 🤖 AI Agent")
    st.markdown("""
- Ask questions in plain English
- Powered by GPT-4o with function calling
- Real-time data queries
- Examples: pay gaps, salary recs, budget costs
    """)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("### 💰 Salary Increase Simulator")
    st.markdown("""
- Interactive merit matrix (editable grid)
- Budget utilization tracking
- Cost by department
- Before/after compa-ratio analysis
    """)

with col5:
    st.markdown("### 🚀 Promotion Calculator")
    st.markdown("""
- Salary recommendation for target grade
- Market P25/P50/P75 positioning
- Annual and monthly cost impact
- Budget % of department payroll
    """)

with col6:
    st.markdown("### 🎯 STI Tool")
    st.markdown("""
- Configurable performance multipliers
- Target vs actual payout analysis
- Outlier flagging
- Department and grade breakdown
    """)

st.divider()
st.markdown("""
> **About this platform:** CompIQ was built to demonstrate compensation analytics capabilities
> aligned with the Sasol Rewards Analyst role. It covers the full scope of the role:
> market benchmarking, pay equity analysis, STI/LTI support, promotion tooling, and AI-assisted
> analytics — exactly as described in the job description key accountabilities.
""")
