"""
Page 1: Executive Dashboard
KPIs, compa-ratio overview, risk flags, country breakdown.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.generate_data import load_or_generate
from utils.compensation import enrich_with_market
from utils.charts import (
    compa_ratio_distribution, market_position_pie,
    compa_by_country, gender_gap_heatmap
)

st.set_page_config(page_title="Dashboard | CompIQ", layout="wide")

@st.cache_data
def get_data():
    emp, mkt, sti = load_or_generate()
    return enrich_with_market(emp, mkt), mkt, sti

df, market, sti = get_data()

st.title("CompIQ — Compensation Intelligence Platform")
st.caption("Sasol International Chemicals | Rewards Analytics Dashboard")
st.divider()

# ── KPI Row ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

avg_compa = df["compa_ratio"].mean()
below_market = (df["compa_ratio"] < 0.90).sum()
overpaid = df["overpaid_flag"].sum()
gender_gap = (
    (df[df["gender"] == "Male"]["base_salary"].mean() -
     df[df["gender"] == "Female"]["base_salary"].mean()) /
    df[df["gender"] == "Male"]["base_salary"].mean() * 100
)
retention_risk_pct = below_market / len(df) * 100

k1.metric("Avg Compa-Ratio", f"{avg_compa:.3f}",
          delta=f"{avg_compa - 1:.3f} vs Market",
          delta_color="normal")
k2.metric("Below Market (< 0.90)", f"{below_market}",
          delta=f"{retention_risk_pct:.1f}% of workforce",
          delta_color="inverse")
k3.metric("Above P90 (Overpaid)", str(overpaid))
k4.metric("Overall Gender Pay Gap", f"{gender_gap:.1f}%",
          delta="M vs F mean salary",
          delta_color="inverse")
k5.metric("Total Employees", str(len(df)))

st.divider()

# ── Charts Row 1 ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(compa_ratio_distribution(df), use_container_width=True)
with col2:
    st.plotly_chart(market_position_pie(df), use_container_width=True)

# ── Charts Row 2 ─────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(compa_by_country(df), use_container_width=True)
with col4:
    st.plotly_chart(gender_gap_heatmap(df), use_container_width=True)

# ── Risk Table ────────────────────────────────────────────────────────────────
st.subheader("Retention Risk Employees (Compa-Ratio < 0.90)")
risk_df = df[df["retention_risk"]].sort_values("compa_ratio")[
    ["employee_id", "name", "country", "department", "job_family",
     "grade", "base_salary", "currency", "compa_ratio", "performance_rating"]
].reset_index(drop=True)
st.dataframe(risk_df, use_container_width=True, height=280)
