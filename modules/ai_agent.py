"""
AI Compensation Agent powered by OpenAI API with function calling.
The agent calls real Python functions to answer compensation questions.
"""

import openai
import json
import numpy as np
import pandas as pd
from typing import Any


class _NumpyEncoder(json.JSONEncoder):
    """Make numpy types JSON-serializable."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# ── Tool Definitions (OpenAI function calling format) ──────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_gender_pay_gap",
            "description": "Compute gender pay gap statistics. Can group by department, grade, or country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": "string",
                        "enum": ["overall", "department", "grade", "country"],
                        "description": "How to group the analysis"
                    }
                },
                "required": ["group_by"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_employees_below_market",
            "description": "Find employees whose salary is below market percentile threshold.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Filter by country (optional, use 'all' for all countries)"},
                    "threshold": {"type": "number", "description": "Compa-ratio threshold, default 0.90 (below P25 equivalent)"}
                },
                "required": ["country", "threshold"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_salary_budget_cost",
            "description": "Calculate the total cost of applying a salary increase budget percentage to a country or all.",
            "parameters": {
                "type": "object",
                "properties": {
                    "increase_pct": {"type": "number", "description": "Salary increase percentage e.g. 4.0 for 4%"},
                    "country": {"type": "string", "description": "Country to apply to, or 'all' for global"}
                },
                "required": ["increase_pct", "country"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_salary_recommendation",
            "description": "Get a salary recommendation for a specific grade, job family, and country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "grade": {"type": "integer", "description": "Job grade (1-8)"},
                    "job_family": {"type": "string", "description": "Job family e.g. Manager, Analyst, Engineer"},
                    "country": {"type": "string", "description": "Country"}
                },
                "required": ["grade", "job_family", "country"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_department_summary",
            "description": "Get compensation summary statistics for a specific department or all departments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department": {"type": "string", "description": "Department name or 'all' for all departments"}
                },
                "required": ["department"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sti_summary",
            "description": "Get STI (Short-Term Incentive) payout summary by grade or department.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {"type": "string", "enum": ["grade", "department", "country"], "description": "Grouping dimension"}
                },
                "required": ["group_by"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_retention_risk_summary",
            "description": "Get a summary of employees at retention risk (below market threshold) by department or country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {"type": "string", "enum": ["department", "country", "grade"], "description": "Grouping"}
                },
                "required": ["group_by"]
            }
        }
    }
]


class CompensationAgent:
    def __init__(self, enriched_df: pd.DataFrame, market_df: pd.DataFrame, sti_df: pd.DataFrame):
        self.df = enriched_df
        self.market = market_df
        self.sti = sti_df
        self.client = openai.OpenAI()

    # ── Tool Implementations ───────────────────────────────────────────────────
    def _get_gender_pay_gap(self, group_by: str) -> dict:
        from utils.compensation import compute_gender_gap
        if group_by == "overall":
            result = compute_gender_gap(self.df)
        else:
            result = compute_gender_gap(self.df, group_by=[group_by])
        return result.to_dict(orient="records")

    def _get_employees_below_market(self, country: str, threshold: float) -> dict:
        filtered = self.df if country.lower() == "all" else self.df[self.df["country"] == country]
        below = filtered[filtered["compa_ratio"] < threshold][
            ["employee_id", "name", "country", "department", "grade",
             "base_salary", "currency", "compa_ratio", "performance_rating"]
        ].sort_values("compa_ratio")
        return {
            "count": len(below),
            "country": country,
            "threshold": threshold,
            "employees": below.head(20).to_dict(orient="records")
        }

    def _get_salary_budget_cost(self, increase_pct: float, country: str) -> dict:
        filtered = self.df if country.lower() == "all" else self.df[self.df["country"] == country]
        total_payroll = filtered["base_salary"].sum()
        total_cost = total_payroll * (increase_pct / 100)
        by_dept = filtered.groupby("department")["base_salary"].sum() * (increase_pct / 100)
        return {
            "country": country,
            "increase_pct": increase_pct,
            "total_current_payroll": round(total_payroll, 0),
            "total_increase_cost": round(total_cost, 0),
            "headcount": len(filtered),
            "cost_by_department": {k: round(v, 0) for k, v in by_dept.items()}
        }

    def _get_salary_recommendation(self, grade: int, job_family: str, country: str) -> dict:
        mkt = self.market[
            (self.market["grade"] == grade) &
            (self.market["job_family"] == job_family) &
            (self.market["country"] == country)
        ]
        if mkt.empty:
            return {"error": f"No market data for Grade {grade} {job_family} in {country}"}
        row = mkt.iloc[0]
        return {
            "grade": grade, "job_family": job_family, "country": country,
            "currency": row["currency"],
            "p25": row["p25"], "p50": row["p50"],
            "p75": row["p75"], "p90": row["p90"],
            "recommendation": f"For Grade {grade} {job_family} in {country}, recommend salary between {row['p25']:,.0f}–{row['p75']:,.0f} {row['currency']} (market range P25–P75), with midpoint at {row['p50']:,.0f} {row['currency']}."
        }

    def _get_department_summary(self, department: str) -> dict:
        filtered = self.df if department.lower() == "all" else self.df[self.df["department"] == department]
        summary = {
            "department": department,
            "headcount": len(filtered),
            "avg_salary": round(filtered["base_salary"].mean(), 0),
            "avg_compa_ratio": round(filtered["compa_ratio"].mean(), 3),
            "below_market_count": int((filtered["compa_ratio"] < 0.90).sum()),
            "gender_split": filtered["gender"].value_counts().to_dict(),
            "avg_performance": round(filtered["performance_rating"].mean(), 2),
            "grade_distribution": filtered["grade"].value_counts().sort_index().to_dict()
        }
        return summary

    def _get_sti_summary(self, group_by: str) -> dict:
        from utils.compensation import calculate_sti
        default_multipliers = {5: 1.5, 4: 1.2, 3: 1.0, 2: 0.5, 1: 0.0}
        result = calculate_sti(self.df, self.sti, default_multipliers)
        summary = result.groupby(group_by).agg(
            headcount=("employee_id", "count"),
            total_target=("sti_target_amount", "sum"),
            total_payout=("sti_payout", "sum"),
            avg_payout=("sti_payout", "mean")
        ).round(0).reset_index()
        return summary.to_dict(orient="records")

    def _get_retention_risk_summary(self, group_by: str) -> dict:
        risk = self.df[self.df["retention_risk"]]
        summary = risk.groupby(group_by).agg(
            at_risk=("employee_id", "count"),
            avg_compa_ratio=("compa_ratio", "mean")
        ).round(3).reset_index()
        total = self.df.groupby(group_by)["employee_id"].count().reset_index()
        total.columns = [group_by, "total"]
        merged = summary.merge(total, on=group_by)
        merged["risk_pct"] = (merged["at_risk"] / merged["total"] * 100).round(1)
        return merged.to_dict(orient="records")

    def _execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        dispatch = {
            "get_gender_pay_gap": lambda: self._get_gender_pay_gap(**tool_input),
            "get_employees_below_market": lambda: self._get_employees_below_market(**tool_input),
            "get_salary_budget_cost": lambda: self._get_salary_budget_cost(**tool_input),
            "get_salary_recommendation": lambda: self._get_salary_recommendation(**tool_input),
            "get_department_summary": lambda: self._get_department_summary(**tool_input),
            "get_sti_summary": lambda: self._get_sti_summary(**tool_input),
            "get_retention_risk_summary": lambda: self._get_retention_risk_summary(**tool_input),
        }
        if tool_name not in dispatch:
            return {"error": f"Unknown tool: {tool_name}"}
        return dispatch[tool_name]()

    # ── Main Chat Method ───────────────────────────────────────────────────────
    def chat(self, messages: list) -> tuple[str, list]:
        """
        Send messages to OpenAI, handle tool_calls loop, return (response_text, updated_messages).
        """
        system_prompt = """You are CompIQ, an expert AI compensation analyst for Sasol International Chemicals.
You have access to live compensation data for 500 employees across Germany, USA, UK, Singapore, and South Africa.

Your role:
- Answer questions about salaries, market benchmarks, gender pay gaps, STI payouts, and retention risk
- Use your tools to query the live data — never make up numbers
- Provide clear, concise answers suitable for an HR professional or business leader
- Reference specific numbers, percentages, and employee counts when answering
- Mention currencies (EUR, USD, GBP, SGD, ZAR) when discussing salaries

Always use tools to get accurate data. Be professional and direct."""

        updated_messages = [{"role": "system", "content": system_prompt}] + messages.copy()

        response = self.client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2048,
            tools=TOOLS,
            messages=updated_messages
        )

        while response.choices[0].finish_reason == "tool_calls":
            assistant_message = response.choices[0].message
            updated_messages.append(assistant_message)

            for tool_call in assistant_message.tool_calls:
                tool_input = json.loads(tool_call.function.arguments)
                tool_result = self._execute_tool(tool_call.function.name, tool_input)
                updated_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, cls=_NumpyEncoder)
                })

            response = self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2048,
                tools=TOOLS,
                messages=updated_messages
            )

        final_text = response.choices[0].message.content or ""
        updated_messages.append({"role": "assistant", "content": final_text})

        # Return only simple string-content messages (strip system prompt)
        simple_messages = [
            m for m in updated_messages[1:]  # skip system message
            if isinstance(m, dict) and isinstance(m.get("content"), str)
            and m.get("role") in ("user", "assistant")
        ]
        return final_text, simple_messages
