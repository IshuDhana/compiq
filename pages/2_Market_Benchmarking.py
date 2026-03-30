"""
Page 2: Market Benchmarking
Filter employees, view compa-ratios vs market, export to Excel.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.generate_data import load_or_generate
from utils.compensation import enrich_with_market

st.set_page_config(page_title="Market Benchmarking | CompIQ", layout="wide")

@st.cache_data
def get_data():
    emp, mkt, sti = load_or_generate()
    return enrich_with_market(emp, mkt), mkt

df, market = get_data()

st.title("Market Benchmarking")
st.caption("Compare internal salaries against external market data (P25/P50/P75/P90)")
st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
f1, f2, f3, f4 = st.columns(4)
countries = f1.multiselect("Country", df["country"].unique(), default=list(df["country"].unique()))
departments = f2.multiselect("Department", df["department"].unique(), default=list(df["department"].unique()))
grades = f3.multiselect("Grade", sorted(df["grade"].unique()), default=sorted(df["grade"].unique()))
position_filter = f4.multiselect("Market Position", df["market_position"].cat.categories.tolist(),
                                  default=df["market_position"].cat.categories.tolist())

filtered = df[
    df["country"].isin(countries) &
    df["department"].isin(departments) &
    df["grade"].isin(grades) &
    df["market_position"].isin(position_filter)
].copy()

st.caption(f"Showing {len(filtered)} of {len(df)} employees")

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Avg Compa-Ratio", f"{filtered['compa_ratio'].mean():.3f}")
k2.metric("Below P25", str((filtered["compa_ratio"] < 0.88).sum()))
k3.metric("At Market (0.95–1.05)", str(((filtered["compa_ratio"] >= 0.95) & (filtered["compa_ratio"] <= 1.05)).sum()))
k4.metric("Above P90", str(filtered["overpaid_flag"].sum()))

st.divider()

# ── Scatter: Salary vs Market P50 ─────────────────────────────────────────────
st.subheader("Salary vs Market Midpoint (P50) — by Grade")
fig = px.scatter(
    filtered, x="p50", y="base_salary",
    color="market_position", symbol="gender",
    hover_data=["name", "country", "department", "compa_ratio"],
    labels={"p50": "Market P50", "base_salary": "Actual Salary"},
    color_discrete_sequence=["#E8380D","#4A90D9","#7ED321","#F5A623","#9B9B9B"],
    title="Actual Salary vs Market Midpoint"
)
# Add 45-degree reference line
max_val = max(filtered["p50"].max(), filtered["base_salary"].max())
fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
              line=dict(dash="dash", color="gray"))
fig.update_layout(height=430)
st.plotly_chart(fig, use_container_width=True)

# ── Box plot by grade ─────────────────────────────────────────────────────────
st.subheader("Compa-Ratio Distribution by Grade")
fig2 = px.box(
    filtered, x="grade", y="compa_ratio",
    color="gender",
    color_discrete_sequence=["#1A3A5C", "#E8380D"],
    points="outliers",
    title="Compa-Ratio by Grade and Gender"
)
fig2.add_hline(y=1.0, line_dash="dash", line_color="green", annotation_text="Market Mid")
fig2.add_hline(y=0.90, line_dash="dot", line_color="red", annotation_text="Risk Threshold")
fig2.update_layout(height=380)
st.plotly_chart(fig2, use_container_width=True)

# ── Data Table ────────────────────────────────────────────────────────────────
st.subheader("Employee Detail")
display_cols = ["employee_id", "name", "gender", "country", "department",
                "job_family", "grade", "base_salary", "currency",
                "p25", "p50", "p75", "compa_ratio", "market_position",
                "performance_rating", "retention_risk"]

st.dataframe(
    filtered[display_cols].sort_values("compa_ratio").reset_index(drop=True),
    use_container_width=True, height=350,
    column_config={
        "compa_ratio": st.column_config.ProgressColumn("Compa-Ratio", min_value=0, max_value=1.5, format="%.3f"),
        "retention_risk": st.column_config.CheckboxColumn("Retention Risk"),
    }
)

# ── Export ────────────────────────────────────────────────────────────────────
if st.button("Export to Excel"):
    import io
    buf = io.BytesIO()
    filtered[display_cols].to_excel(buf, index=False, engine="openpyxl")
    st.download_button("Download Excel", buf.getvalue(),
                       file_name="benchmarking_export.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
