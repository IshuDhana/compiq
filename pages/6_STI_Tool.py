"""
Page 6: STI (Short-Term Incentive) Allocation Tool
Calculate bonus payouts, view cost by department/country, flag outliers.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os, io

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.generate_data import load_or_generate
from utils.compensation import enrich_with_market, calculate_sti
from utils.charts import sti_distribution

st.set_page_config(page_title="STI Tool | CompIQ", layout="wide")

@st.cache_data
def get_data():
    emp, mkt, sti = load_or_generate()
    return enrich_with_market(emp, mkt), sti

df, sti_targets = get_data()

st.title("STI Allocation Tool")
st.caption("Short-Term Incentive payout calculation with performance multipliers")
st.divider()

# ── Performance Multipliers ────────────────────────────────────────────────────
st.subheader("Performance Multipliers")
st.caption("Set payout multiplier per performance rating (1.0 = 100% of target, 1.5 = 150%)")

col1, col2 = st.columns(2)
with col1:
    m5 = st.slider("Rating 5 — Outstanding", 0.0, 2.0, 1.5, 0.05)
    m4 = st.slider("Rating 4 — Exceeds Expectations", 0.0, 2.0, 1.2, 0.05)
    m3 = st.slider("Rating 3 — Meets Expectations", 0.0, 2.0, 1.0, 0.05)

with col2:
    m2 = st.slider("Rating 2 — Partially Meets", 0.0, 2.0, 0.5, 0.05)
    m1 = st.slider("Rating 1 — Does Not Meet", 0.0, 1.0, 0.0, 0.05)

perf_multipliers = {5: m5, 4: m4, 3: m3, 2: m2, 1: m1}

# ── Scope Filter ──────────────────────────────────────────────────────────────
f1, f2 = st.columns(2)
countries = f1.multiselect("Countries", df["country"].unique(), default=list(df["country"].unique()))
departments = f2.multiselect("Departments", df["department"].unique(), default=list(df["department"].unique()))
scope = df[df["country"].isin(countries) & df["department"].isin(departments)].copy()

st.divider()

if st.button("Calculate STI Payouts", type="primary"):
    result = calculate_sti(scope, sti_targets, perf_multipliers)

    # KPIs
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total STI Target", f"{result['sti_target_amount'].sum():,.0f}")
    k2.metric("Total STI Payout", f"{result['sti_payout'].sum():,.0f}")
    k3.metric("Payout vs Target", f"{(result['sti_payout'].sum() / result['sti_target_amount'].sum() * 100):.1f}%")
    k4.metric("Outliers Flagged", str(result["sti_outlier"].sum()))
    k5.metric("Zero Payout Employees", str((result["sti_payout"] == 0).sum()))

    tab1, tab2, tab3 = st.tabs(["By Department", "By Grade", "Employee Detail"])

    with tab1:
        dept_sum = result.groupby("department").agg(
            headcount=("employee_id", "count"),
            total_target=("sti_target_amount", "sum"),
            total_payout=("sti_payout", "sum")
        ).reset_index()
        dept_sum["payout_vs_target_pct"] = (dept_sum["total_payout"] / dept_sum["total_target"] * 100).round(1)
        fig = px.bar(
            dept_sum.sort_values("total_payout", ascending=False),
            x="department", y=["total_target", "total_payout"],
            barmode="group",
            title="STI: Target vs Actual Payout by Department",
            color_discrete_sequence=["#9B9B9B", "#E8380D"]
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(dept_sum, use_container_width=True)

    with tab2:
        st.plotly_chart(sti_distribution(result), use_container_width=True)
        grade_sum = result.groupby("grade").agg(
            headcount=("employee_id", "count"),
            sti_target_pct=("sti_target_pct", "first"),
            avg_payout=("sti_payout", "mean"),
            total_payout=("sti_payout", "sum")
        ).reset_index()
        st.dataframe(grade_sum, use_container_width=True)

    with tab3:
        display_cols = ["employee_id", "name", "country", "department", "grade",
                        "base_salary", "currency", "sti_target_pct", "performance_rating",
                        "perf_multiplier", "sti_target_amount", "sti_payout",
                        "sti_vs_target_pct", "sti_outlier"]
        st.dataframe(
            result[display_cols].sort_values("sti_payout", ascending=False).reset_index(drop=True),
            use_container_width=True, height=400,
            column_config={
                "sti_outlier": st.column_config.CheckboxColumn("Outlier"),
                "sti_vs_target_pct": st.column_config.ProgressColumn("vs Target %", min_value=0, max_value=200, format="%.0f%%")
            }
        )

        # Export
        buf = io.BytesIO()
        result[display_cols].to_excel(buf, index=False, engine="openpyxl")
        st.download_button("Export STI Results to Excel", buf.getvalue(),
                           file_name="sti_allocation.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
