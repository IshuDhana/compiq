"""
Page 4: Annual Salary Increase Simulator
Interactive merit matrix, budget simulation, cost impact analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sys, os, io

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.generate_data import load_or_generate
from utils.compensation import enrich_with_market, apply_merit_matrix, default_merit_matrix
from utils.charts import salary_increase_waterfall

st.set_page_config(page_title="Salary Increase Simulator | CompIQ", layout="wide")

@st.cache_data
def get_data():
    emp, mkt, sti = load_or_generate()
    return enrich_with_market(emp, mkt)

df = get_data()

st.title("Annual Salary Increase Simulator")
st.caption("Design your merit matrix and simulate the cost of annual salary increases")
st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
f1, f2 = st.columns(2)
countries = f1.multiselect("Country Scope", df["country"].unique(), default=list(df["country"].unique()))
budget_pct = f2.slider("Overall Budget Target (%)", min_value=1.0, max_value=10.0, value=3.5, step=0.1)

scope_df = df[df["country"].isin(countries)].copy()

st.divider()

# ── Editable Merit Matrix ─────────────────────────────────────────────────────
st.subheader("Merit Matrix (%) — Edit Increase % per Cell")
st.caption("Rows = Performance Rating (1=Low, 5=High) | Columns = Market Position")

market_positions = ["Below P25", "P25-P50", "At Market", "P50-P75", "Above P75"]
perf_ratings = [5, 4, 3, 2, 1]
default_matrix = default_merit_matrix()

# Build editable DataFrame
matrix_data = []
for p in perf_ratings:
    row = {"Performance": p}
    for mp in market_positions:
        row[mp] = default_matrix.get((p, mp), 0.0)
    matrix_data.append(row)

matrix_df = pd.DataFrame(matrix_data).set_index("Performance")

edited = st.data_editor(
    matrix_df,
    use_container_width=True,
    num_rows="fixed",
    column_config={mp: st.column_config.NumberColumn(mp, min_value=0.0, max_value=20.0, step=0.5, format="%.1f%%")
                   for mp in market_positions}
)

# Rebuild matrix dict
user_matrix = {}
for p in perf_ratings:
    for mp in market_positions:
        user_matrix[(p, mp)] = float(edited.loc[p, mp])

st.divider()

# ── Run Simulation ─────────────────────────────────────────────────────────────
if st.button("Run Simulation", type="primary"):
    result = apply_merit_matrix(scope_df, budget_pct, user_matrix)

    total_current = result["base_salary"].sum()
    total_increase = result["increase_amount"].sum()
    total_new = result["new_salary"].sum()
    actual_budget_pct = (total_increase / total_current) * 100

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Current Payroll", f"{total_current:,.0f}")
    k2.metric("Total Increase Cost", f"{total_increase:,.0f}")
    k3.metric("Actual Budget Used", f"{actual_budget_pct:.2f}%",
              delta=f"{actual_budget_pct - budget_pct:.2f}% vs target",
              delta_color="inverse" if actual_budget_pct > budget_pct else "normal")
    k4.metric("Avg Compa-Ratio Before", f"{result['compa_ratio'].mean():.3f}")
    k5.metric("Avg Compa-Ratio After", f"{result['new_compa_ratio'].mean():.3f}")

    col1, col2 = st.columns(2)
    with col1:
        # Cost by department
        dept_cost = result.groupby("department").agg(
            total_increase=("increase_amount", "sum"),
            headcount=("employee_id", "count")
        ).reset_index().sort_values("total_increase", ascending=False)
        fig = px.bar(dept_cost, x="department", y="total_increase",
                     title="Increase Cost by Department",
                     color="total_increase", color_continuous_scale="Blues",
                     labels={"total_increase": "Total Increase Cost"})
        fig.update_layout(height=380, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Compa-ratio shift
        before_avg = result["compa_ratio"].mean()
        after_avg = result["new_compa_ratio"].mean()
        increase_avg = after_avg - before_avg
        st.plotly_chart(
            salary_increase_waterfall(before_avg, increase_avg, after_avg, "Compa-Ratio"),
            use_container_width=True
        )

    # By performance rating summary
    st.subheader("Summary by Performance Rating")
    perf_summary = result.groupby("performance_rating").agg(
        headcount=("employee_id", "count"),
        avg_merit_pct=("merit_pct", "mean"),
        total_cost=("increase_amount", "sum"),
        avg_new_compa=("new_compa_ratio", "mean")
    ).reset_index()
    perf_summary.columns = ["Performance", "Headcount", "Avg Merit %", "Total Cost", "Avg New Compa-Ratio"]
    st.dataframe(perf_summary, use_container_width=True)

    # Export
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        result[[
            "employee_id", "name", "country", "department", "grade",
            "base_salary", "merit_pct", "increase_amount", "new_salary",
            "compa_ratio", "new_compa_ratio", "performance_rating"
        ]].to_excel(writer, sheet_name="Increase Details", index=False)
        perf_summary.to_excel(writer, sheet_name="Summary by Performance", index=False)
        dept_cost.to_excel(writer, sheet_name="Summary by Department", index=False)

    st.download_button(
        "Export Results to Excel",
        buf.getvalue(),
        file_name="salary_increase_simulation.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
