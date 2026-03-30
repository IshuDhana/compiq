"""
Page 5: Promotion Cost Impact Calculator
Input a promotion scenario and get a salary recommendation with full cost breakdown.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.generate_data import load_or_generate, CURRENCY_MAP
from utils.compensation import enrich_with_market, promotion_recommendation

st.set_page_config(page_title="Promotion Calculator | CompIQ", layout="wide")

@st.cache_data
def get_data():
    emp, mkt, sti = load_or_generate()
    return enrich_with_market(emp, mkt), mkt

df, market = get_data()

st.title("Promotion Cost Impact Calculator")
st.caption("Get a data-driven salary recommendation and cost impact for any promotion scenario")
st.divider()

# ── Input Form ────────────────────────────────────────────────────────────────
st.subheader("Promotion Scenario")

col1, col2 = st.columns(2)
with col1:
    country = st.selectbox("Country", sorted(df["country"].unique()))
    job_family = st.selectbox("Job Family", sorted(df["job_family"].unique()))
    current_grade = st.selectbox("Current Grade", list(range(1, 8)), index=2)
    target_grade = st.selectbox("Target Grade (Promotion To)", list(range(2, 9)), index=3)

with col2:
    currency = CURRENCY_MAP[country][0]
    current_salary = st.number_input(
        f"Current Salary ({currency})", min_value=10000, max_value=500000,
        value=int(df[(df["country"] == country) & (df["grade"] == current_grade)]["base_salary"].median()),
        step=500
    )
    dept_payroll = st.number_input(
        f"Department Annual Payroll ({currency})", min_value=100000, max_value=50000000,
        value=2000000, step=10000
    )
    performance = st.selectbox("Employee Performance Rating", [1, 2, 3, 4, 5], index=3)

if target_grade <= current_grade:
    st.error("Target grade must be higher than current grade for a promotion.")
    st.stop()

# ── Calculate ─────────────────────────────────────────────────────────────────
result = promotion_recommendation(
    current_grade, current_salary, target_grade,
    country, job_family, market
)

if "error" in result:
    st.error(result["error"])
    st.stop()

st.divider()
st.subheader("Recommendation")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Recommended Salary", f"{result['recommended_salary']:,.0f} {result['currency']}")
k2.metric("New Compa-Ratio", f"{result['new_compa_ratio']:.3f}",
          delta="At Market" if 0.95 <= result['new_compa_ratio'] <= 1.05 else
          ("Above Market" if result['new_compa_ratio'] > 1.05 else "Below Market"))
k3.metric("Annual Cost Increase", f"{result['annual_cost_increase']:,.0f} {result['currency']}")
k4.metric("Monthly Cost Increase", f"{result['monthly_cost_increase']:,.0f} {result['currency']}")

if result["below_market_p25"]:
    st.warning("Recommended salary is below market P25 for the target grade. Consider increasing.")

# ── Salary Range Gauge ────────────────────────────────────────────────────────
st.subheader("Target Grade Market Range")
col1, col2 = st.columns([2, 1])
with col1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["P25", "P50 (Mid)", "P75", "Recommended"],
        y=[result["market_p25"], result["market_p50"], result["market_p75"], result["recommended_salary"]],
        marker_color=["#9B9B9B", "#4A90D9", "#9B9B9B", "#E8380D"],
        text=[f"{v:,.0f}" for v in [result["market_p25"], result["market_p50"], result["market_p75"], result["recommended_salary"]]],
        textposition="outside"
    ))
    fig.update_layout(
        title=f"Salary Positioning — Grade {target_grade} | {job_family} | {country}",
        yaxis_title=f"Salary ({result['currency']})", height=380, showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Cost Summary")
    budget_pct = (result["annual_cost_increase"] / dept_payroll) * 100
    st.metric("Budget Impact", f"{budget_pct:.2f}% of dept payroll")
    st.metric("Current Salary", f"{current_salary:,.0f} {result['currency']}")
    st.metric("Recommended New Salary", f"{result['recommended_salary']:,.0f} {result['currency']}")
    st.metric("Market P25 (Target Grade)", f"{result['market_p25']:,.0f} {result['currency']}")
    st.metric("Market P50 (Target Grade)", f"{result['market_p50']:,.0f} {result['currency']}")
    st.metric("Market P75 (Target Grade)", f"{result['market_p75']:,.0f} {result['currency']}")

    if performance == 5:
        st.info("Top performer — consider targeting closer to P75 to retain talent.")
    elif performance <= 2:
        st.warning("Below-average performer — standard promotion minimum (P25) recommended.")

# ── Bulk Promotions ────────────────────────────────────────────────────────────
st.divider()
st.subheader("Bulk Promotion Batch (Upload List)")

REQUIRED_COLS = ["employee_id", "country", "job_family", "current_grade", "target_grade", "current_salary"]

# Offer a sample template to download
import io as _io
sample = pd.DataFrame([
    {"employee_id": "EMP1001", "country": "Germany", "job_family": "Manager",
     "current_grade": 3, "target_grade": 4, "current_salary": 65000},
    {"employee_id": "EMP1002", "country": "USA", "job_family": "Analyst",
     "current_grade": 2, "target_grade": 3, "current_salary": 52000},
])
sample_buf = _io.BytesIO()
sample.to_csv(sample_buf, index=False)
st.download_button("Download Sample CSV Template", sample_buf.getvalue(),
                   file_name="promotion_batch_template.csv", mime="text/csv")

st.caption(f"Required columns: {', '.join(REQUIRED_COLS)}")
uploaded = st.file_uploader("Upload CSV", type=["csv"])
if uploaded:
    batch = pd.read_csv(uploaded)
    missing_cols = [c for c in REQUIRED_COLS if c not in batch.columns]
    if missing_cols:
        st.error(f"Missing required columns: **{', '.join(missing_cols)}**\n\nFound: {list(batch.columns)}")
        st.info("Download the sample template above to see the correct format.")
    else:
        results = []
        for _, row in batch.iterrows():
            r = promotion_recommendation(
                int(row["current_grade"]), float(row["current_salary"]),
                int(row["target_grade"]), row["country"], row["job_family"], market
            )
            r["employee_id"] = row["employee_id"]
            results.append(r)
        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True)
        buf = _io.BytesIO()
        results_df.to_excel(buf, index=False, engine="openpyxl")
        st.download_button("Download Batch Results", buf.getvalue(),
                           file_name="promotion_batch_results.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
