"""
Reusable Plotly chart builders for the compensation dashboard.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


SASOL_COLORS = ["#E8380D", "#1A3A5C", "#4A90D9", "#F5A623", "#7ED321", "#9B9B9B"]


def compa_ratio_distribution(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        df, x="compa_ratio", nbins=40,
        color_discrete_sequence=[SASOL_COLORS[2]],
        title="Compa-Ratio Distribution",
        labels={"compa_ratio": "Compa-Ratio"}
    )
    fig.add_vline(x=1.0, line_dash="dash", line_color=SASOL_COLORS[0],
                  annotation_text="Market Mid (1.0)")
    fig.add_vline(x=0.90, line_dash="dot", line_color=SASOL_COLORS[3],
                  annotation_text="Risk Threshold (0.90)")
    fig.update_layout(showlegend=False, height=350)
    return fig


def market_position_pie(df: pd.DataFrame) -> go.Figure:
    counts = df["market_position"].value_counts().reset_index()
    counts.columns = ["position", "count"]
    fig = px.pie(
        counts, names="position", values="count",
        title="Employees by Market Position",
        color_discrete_sequence=SASOL_COLORS
    )
    fig.update_layout(height=350)
    return fig


def gender_gap_bar(gap_df: pd.DataFrame, group_col: str) -> go.Figure:
    if group_col not in gap_df.columns:
        return go.Figure()
    fig = px.bar(
        gap_df.sort_values("mean_gap_pct", ascending=False),
        x=group_col, y="mean_gap_pct",
        color="significant",
        color_discrete_map={True: SASOL_COLORS[0], False: SASOL_COLORS[5]},
        title=f"Gender Pay Gap (Mean %) by {group_col.title()}",
        labels={"mean_gap_pct": "Pay Gap %", "significant": "Statistically Significant"},
        text="mean_gap_pct"
    )
    fig.add_hline(y=0, line_color="black")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=400)
    return fig


def gender_gap_heatmap(df: pd.DataFrame) -> go.Figure:
    pivot = df.pivot_table(
        index="department", columns="grade",
        values="compa_ratio", aggfunc="mean"
    ).round(3)
    fig = px.imshow(
        pivot, text_auto=True,
        color_continuous_scale="RdYlGn",
        title="Average Compa-Ratio by Department & Grade",
        labels={"color": "Avg Compa-Ratio"}
    )
    fig.update_layout(height=420)
    return fig


def salary_increase_waterfall(before_avg: float, increase_avg: float, after_avg: float, currency: str = "") -> go.Figure:
    fig = go.Figure(go.Waterfall(
        name="Salary Movement",
        orientation="v",
        measure=["absolute", "relative", "total"],
        x=["Before Increase", "Merit Increase", "After Increase"],
        y=[before_avg, increase_avg, after_avg],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": SASOL_COLORS[4]}},
        totals={"marker": {"color": SASOL_COLORS[1]}},
    ))
    fig.update_layout(
        title=f"Average Salary Movement {currency}",
        height=350, showlegend=False
    )
    return fig


def sti_distribution(df: pd.DataFrame) -> go.Figure:
    fig = px.box(
        df, x="grade", y="sti_payout",
        color_discrete_sequence=[SASOL_COLORS[1]],
        title="STI Payout Distribution by Grade",
        labels={"sti_payout": "STI Payout", "grade": "Grade"}
    )
    fig.update_layout(height=380)
    return fig


def compa_by_country(df: pd.DataFrame) -> go.Figure:
    avg = df.groupby("country")["compa_ratio"].mean().reset_index()
    avg.columns = ["country", "avg_compa_ratio"]
    fig = px.bar(
        avg.sort_values("avg_compa_ratio"),
        x="avg_compa_ratio", y="country", orientation="h",
        color="avg_compa_ratio",
        color_continuous_scale="RdYlGn",
        title="Average Compa-Ratio by Country",
        labels={"avg_compa_ratio": "Avg Compa-Ratio"}
    )
    fig.add_vline(x=1.0, line_dash="dash", line_color="gray")
    fig.update_layout(height=350, coloraxis_showscale=False)
    return fig
