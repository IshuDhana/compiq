"""
Page 3: Gender Pay Gap Analysis
Statistical analysis, visualizations, and auto-generated executive report.
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.generate_data import load_or_generate
from utils.compensation import enrich_with_market, compute_gender_gap
from utils.charts import gender_gap_bar

st.set_page_config(page_title="Gender Pay Gap | CompIQ", layout="wide")

@st.cache_data
def get_data():
    emp, mkt, sti = load_or_generate()
    return enrich_with_market(emp, mkt)

df = get_data()

st.title("Gender Pay Gap Analysis")
st.caption("Pay equity analysis across departments, grades and countries")
st.divider()

# ── Overall Stats ─────────────────────────────────────────────────────────────
overall = compute_gender_gap(df)
if not overall.empty:
    row = overall.iloc[0]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Male Avg Salary", f"{row['male_avg_salary']:,.0f}")
    k2.metric("Female Avg Salary", f"{row['female_avg_salary']:,.0f}")
    k3.metric("Mean Pay Gap", f"{row['mean_gap_pct']:.1f}%",
              delta="Male vs Female", delta_color="inverse")
    k4.metric("Statistically Significant", "Yes" if row["significant"] else "No")

st.divider()

# ── Group Analysis ────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["By Department", "By Grade", "By Country"])

with tab1:
    gap_dept = compute_gender_gap(df, group_by=["department"])
    st.plotly_chart(gender_gap_bar(gap_dept, "department"), use_container_width=True)
    st.dataframe(gap_dept.sort_values("mean_gap_pct", ascending=False), use_container_width=True)

with tab2:
    gap_grade = compute_gender_gap(df, group_by=["grade"])
    st.plotly_chart(gender_gap_bar(gap_grade, "grade"), use_container_width=True)
    st.dataframe(gap_grade.sort_values("grade"), use_container_width=True)

with tab3:
    gap_country = compute_gender_gap(df, group_by=["country"])
    st.plotly_chart(gender_gap_bar(gap_country, "country"), use_container_width=True)
    st.dataframe(gap_country.sort_values("mean_gap_pct", ascending=False), use_container_width=True)

st.divider()

# ── Executive Report ──────────────────────────────────────────────────────────
st.subheader("Auto-Generated Executive Summary Report")

if st.button("Generate Report"):
    gap_dept = compute_gender_gap(df, group_by=["department"])
    gap_country = compute_gender_gap(df, group_by=["country"])
    overall = compute_gender_gap(df)
    row = overall.iloc[0]

    worst_dept = gap_dept.sort_values("mean_gap_pct", ascending=False).iloc[0]
    best_dept = gap_dept.sort_values("mean_gap_pct").iloc[0]
    sig_depts = gap_dept[gap_dept["significant"]]["department"].tolist()

    report = f"""
# Gender Pay Gap Analysis Report
**Date:** {pd.Timestamp.today().strftime('%d %B %Y')}
**Scope:** International Chemicals — Global (All Countries)
**Prepared by:** Compensation & Rewards Analytics

---

## Executive Summary

The overall mean gender pay gap across Sasol International Chemicals is **{row['mean_gap_pct']:.1f}%**
(male-to-female), with a median gap of **{row['median_gap_pct']:.1f}%**. The gap is
{"**statistically significant** (p = " + str(row['p_value']) + ")" if row['significant']
 else "not statistically significant at the 95% confidence level"}.

A total of **{int(row['male_count'])}** male and **{int(row['female_count'])}** female employees
were included in this analysis.

---

## Key Findings

### 1. Overall Pay Gap
| Metric | Value |
|---|---|
| Male Average Salary | {row['male_avg_salary']:,.0f} (blended currency) |
| Female Average Salary | {row['female_avg_salary']:,.0f} (blended currency) |
| Mean Pay Gap | {row['mean_gap_pct']:.1f}% |
| Median Pay Gap | {row['median_gap_pct']:.1f}% |
| Statistically Significant | {"Yes" if row['significant'] else "No"} |

### 2. Departmental Analysis
- **Highest gap:** {worst_dept['department']} at **{worst_dept['mean_gap_pct']:.1f}%**
- **Lowest gap:** {best_dept['department']} at **{best_dept['mean_gap_pct']:.1f}%**
- Departments with statistically significant gaps: **{', '.join(sig_depts) if sig_depts else 'None'}**

### 3. Grade Distribution
Female employees are {"underrepresented" if df[df["gender"]=="Female"]["grade"].mean() < df[df["gender"]=="Male"]["grade"].mean() else "fairly distributed"}
in senior grades (Grades 6–8), which contributes to the overall pay gap.

---

## Root Cause Assessment

The pay gap is primarily driven by:
1. **Structural representation gap** — fewer women in senior grades (6–8)
2. **Compa-ratio variance** — female employees average compa-ratio:
   {df[df['gender']=='Female']['compa_ratio'].mean():.3f} vs male: {df[df['gender']=='Male']['compa_ratio'].mean():.3f}
3. **Departmental concentration** — higher proportion of female employees in lower-grade roles in certain departments

---

## Recommendations

1. **Immediate Review:** Conduct targeted salary reviews for female employees in {', '.join(sig_depts[:3]) if sig_depts else 'key departments'} where gaps are statistically significant
2. **Promotion Pipeline:** Track and report female representation in Grade 5+ promotions quarterly
3. **Hiring Benchmarks:** Ensure new hire offers for female candidates meet at least P50 for the grade
4. **Annual Monitoring:** Include gender pay gap metrics in the annual compensation review cycle
5. **Manager Education:** Brief line managers on unconscious bias in merit increase allocation

---

*This report was generated automatically by CompIQ — Sasol Compensation Intelligence Platform.*
    """
    st.markdown(report)

    # Download
    st.download_button(
        "Download Report (Markdown)",
        report,
        file_name="gender_pay_gap_report.md",
        mime="text/markdown"
    )
