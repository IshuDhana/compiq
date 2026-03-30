"""
Core compensation calculation utilities.
Used across all modules.
"""

import pandas as pd
import numpy as np
from scipy import stats


def enrich_with_market(employees: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    """Join employees with market benchmarks and compute compa-ratio & market position."""
    merged = employees.merge(
        market[["country", "job_family", "grade", "p25", "p50", "p75", "p90"]],
        on=["country", "job_family", "grade"],
        how="left"
    )
    merged["compa_ratio"] = (merged["base_salary"] / merged["p50"]).round(4)
    merged["market_position"] = pd.cut(
        merged["compa_ratio"],
        bins=[0, 0.90, 0.95, 1.05, 1.15, 999],
        labels=["Below P25", "P25-P50", "At Market", "P50-P75", "Above P75"]
    )
    merged["retention_risk"] = merged["compa_ratio"] < 0.90
    merged["overpaid_flag"] = merged["base_salary"] > merged["p90"]
    return merged


def compute_gender_gap(df: pd.DataFrame, group_by: list = None) -> pd.DataFrame:
    """
    Compute mean and median gender pay gap.
    Returns a summary DataFrame with gap % and p-value.
    """
    if group_by is None:
        group_by = []

    results = []

    def _gap_for_group(subset, label_dict):
        male = subset[subset["gender"] == "Male"]["base_salary"]
        female = subset[subset["gender"] == "Female"]["base_salary"]
        if len(male) < 2 or len(female) < 2:
            return None
        mean_gap = ((male.mean() - female.mean()) / male.mean()) * 100
        median_gap = ((male.median() - female.median()) / male.median()) * 100
        t_stat, p_value = stats.ttest_ind(male, female)
        row = {**label_dict,
               "male_count": len(male),
               "female_count": len(female),
               "male_avg_salary": round(male.mean(), 0),
               "female_avg_salary": round(female.mean(), 0),
               "mean_gap_pct": round(mean_gap, 2),
               "median_gap_pct": round(median_gap, 2),
               "p_value": round(p_value, 4),
               "significant": p_value < 0.05}
        return row

    if not group_by:
        row = _gap_for_group(df, {"group": "Overall"})
        if row:
            results.append(row)
    else:
        for keys, subset in df.groupby(group_by):
            if not isinstance(keys, tuple):
                keys = (keys,)
            label_dict = dict(zip(group_by, keys))
            row = _gap_for_group(subset, label_dict)
            if row:
                results.append(row)

    return pd.DataFrame(results)


def apply_merit_matrix(
    df: pd.DataFrame,
    budget_pct: float,
    matrix: dict
) -> pd.DataFrame:
    """
    Apply merit matrix to distribute salary increases.
    matrix: {(perf_rating, market_position_label): increase_pct}
    """
    df = df.copy()
    df["merit_pct"] = df.apply(
        lambda r: matrix.get((r["performance_rating"], str(r["market_position"])), 0.0),
        axis=1
    )
    df["increase_amount"] = (df["base_salary"] * df["merit_pct"] / 100 * df["fte"]).round(0)
    df["new_salary"] = df["base_salary"] + df["increase_amount"]
    df["new_compa_ratio"] = (df["new_salary"] / df["p50"]).round(4)
    return df


def default_merit_matrix() -> dict:
    """
    Standard merit matrix: (performance_rating, market_position) -> increase %
    Higher performers below market get more; high performers above market get less.
    """
    return {
        (5, "Below P25"):  8.0, (5, "P25-P50"):  6.5, (5, "At Market"): 5.0, (5, "P50-P75"): 3.5, (5, "Above P75"): 2.0,
        (4, "Below P25"):  6.0, (4, "P25-P50"):  5.0, (4, "At Market"): 4.0, (4, "P50-P75"): 3.0, (4, "Above P75"): 1.5,
        (3, "Below P25"):  4.0, (3, "P25-P50"):  3.5, (3, "At Market"): 3.0, (3, "P50-P75"): 2.5, (3, "Above P75"): 1.0,
        (2, "Below P25"):  2.0, (2, "P25-P50"):  1.5, (2, "At Market"): 1.0, (2, "P50-P75"): 0.5, (2, "Above P75"): 0.0,
        (1, "Below P25"):  0.0, (1, "P25-P50"):  0.0, (1, "At Market"): 0.0, (1, "P50-P75"): 0.0, (1, "Above P75"): 0.0,
    }


def calculate_sti(df: pd.DataFrame, sti_targets: pd.DataFrame, perf_multipliers: dict) -> pd.DataFrame:
    """
    Calculate STI payouts.
    perf_multipliers: {performance_rating: multiplier}  e.g. {5: 1.5, 4: 1.2, 3: 1.0, 2: 0.5, 1: 0.0}
    """
    df = df.merge(sti_targets, on="grade", how="left")
    df["perf_multiplier"] = df["performance_rating"].map(perf_multipliers)
    df["sti_target_amount"] = (df["base_salary"] * df["sti_target_pct"] / 100 * df["fte"]).round(0)
    df["sti_payout"] = (df["sti_target_amount"] * df["perf_multiplier"]).round(0)
    df["sti_vs_target_pct"] = ((df["sti_payout"] / df["sti_target_amount"]) * 100).round(1)
    df["sti_outlier"] = (df["perf_multiplier"] > 1.4) | (df["perf_multiplier"] == 0.0)
    return df


def promotion_recommendation(
    current_grade: int,
    current_salary: float,
    target_grade: int,
    country: str,
    job_family: str,
    market: pd.DataFrame
) -> dict:
    """Return salary recommendation and cost impact for a promotion."""
    mkt_row = market[
        (market["grade"] == target_grade) &
        (market["country"] == country) &
        (market["job_family"] == job_family)
    ]
    if mkt_row.empty:
        return {"error": "No market data found for this combination."}

    mkt = mkt_row.iloc[0]
    rec_min = mkt["p25"]
    rec_mid = mkt["p50"]
    rec_max = mkt["p75"]

    # Promotion typically brings to at least P25 of new grade or 10% increase, whichever is higher
    min_promoted = max(current_salary * 1.10, rec_min)
    recommended = max(min_promoted, rec_mid * 0.95)

    compa_new = recommended / mkt["p50"]
    annual_cost_increase = recommended - current_salary
    monthly_cost_increase = annual_cost_increase / 12

    return {
        "current_salary": current_salary,
        "recommended_salary": round(recommended, 0),
        "market_p25": mkt["p25"],
        "market_p50": mkt["p50"],
        "market_p75": mkt["p75"],
        "new_compa_ratio": round(compa_new, 3),
        "annual_cost_increase": round(annual_cost_increase, 0),
        "monthly_cost_increase": round(monthly_cost_increase, 0),
        "currency": mkt["currency"],
        "below_market_p25": recommended < mkt["p25"],
    }
