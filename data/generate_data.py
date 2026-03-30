"""
Synthetic HR compensation data generator.
Produces realistic employee, market benchmark, and STI target datasets.
"""

import pandas as pd
import numpy as np
import random
from faker import Faker

fake = Faker()
np.random.seed(42)
random.seed(42)

COUNTRIES = ["Germany", "USA", "UK", "Singapore", "South Africa"]
DEPARTMENTS = ["Engineering", "Finance", "HR", "Sales", "Operations", "Legal", "IT", "Marketing"]
JOB_FAMILIES = ["Analyst", "Engineer", "Manager", "Specialist", "Director", "Consultant", "Coordinator"]
GRADES = list(range(1, 9))
PERFORMANCE_RATINGS = [1, 2, 3, 4, 5]
GENDERS = ["Male", "Female"]

# Base salary midpoints by grade (USD equivalent)
GRADE_SALARY_MID = {
    1: 35000, 2: 45000, 3: 58000, 4: 72000,
    5: 90000, 6: 115000, 7: 145000, 8: 190000
}

# Currency conversion factors relative to USD
CURRENCY_MAP = {
    "Germany": ("EUR", 0.92),
    "USA": ("USD", 1.0),
    "UK": ("GBP", 0.79),
    "Singapore": ("SGD", 1.35),
    "South Africa": ("ZAR", 18.6)
}

# STI target % by grade
STI_TARGETS = {
    1: 5, 2: 7, 3: 10, 4: 12,
    5: 15, 6: 20, 7: 30, 8: 40
}

# Gender pay gap bias (Female salaries slightly lower to simulate real-world gap)
GENDER_BIAS = {"Male": 1.04, "Female": 0.96}


def generate_market_data():
    """Generate market benchmark data (P25/P50/P75/P90) per job family + grade + country."""
    records = []
    for country in COUNTRIES:
        currency, fx = CURRENCY_MAP[country]
        for job_family in JOB_FAMILIES:
            for grade in GRADES:
                base = GRADE_SALARY_MID[grade]
                # Add job family premium
                family_factor = {
                    "Director": 1.25, "Manager": 1.10, "Engineer": 1.08,
                    "Consultant": 1.05, "Analyst": 1.0, "Specialist": 1.02,
                    "Coordinator": 0.90
                }.get(job_family, 1.0)
                mid = base * family_factor * fx
                records.append({
                    "country": country,
                    "currency": currency,
                    "job_family": job_family,
                    "grade": grade,
                    "p25": round(mid * 0.88, 0),
                    "p50": round(mid, 0),
                    "p75": round(mid * 1.12, 0),
                    "p90": round(mid * 1.25, 0),
                })
    return pd.DataFrame(records)


def generate_employees(n=500):
    """Generate synthetic employee dataset."""
    records = []
    emp_id = 1000

    for _ in range(n):
        country = random.choice(COUNTRIES)
        currency, fx = CURRENCY_MAP[country]
        department = random.choice(DEPARTMENTS)
        job_family = random.choice(JOB_FAMILIES)
        grade = random.choices(GRADES, weights=[15, 18, 18, 15, 12, 10, 7, 5])[0]
        gender = random.choice(GENDERS)
        performance = random.choices(PERFORMANCE_RATINGS, weights=[5, 15, 45, 25, 10])[0]

        base_mid = GRADE_SALARY_MID[grade] * fx
        # Salary varies around mid ±20%, with gender bias
        salary = base_mid * random.uniform(0.80, 1.20) * GENDER_BIAS[gender]
        salary = round(salary, 0)

        hire_date = fake.date_between(start_date="-10y", end_date="-6m")
        last_increase = fake.date_between(start_date="-2y", end_date="-3m")
        last_increase_pct = round(random.uniform(1.5, 8.0), 2)
        fte = random.choices([1.0, 0.8, 0.6], weights=[80, 12, 8])[0]

        records.append({
            "employee_id": f"EMP{emp_id}",
            "name": fake.name(),
            "gender": gender,
            "country": country,
            "currency": currency,
            "department": department,
            "job_family": job_family,
            "grade": grade,
            "base_salary": salary,
            "performance_rating": performance,
            "fte": fte,
            "hire_date": hire_date,
            "last_increase_date": last_increase,
            "last_increase_pct": last_increase_pct,
        })
        emp_id += 1

    return pd.DataFrame(records)


def generate_sti_targets():
    """Return STI target % by grade as a DataFrame."""
    return pd.DataFrame([
        {"grade": g, "sti_target_pct": t} for g, t in STI_TARGETS.items()
    ])


def load_or_generate():
    """Load cached data or regenerate if not present."""
    import os
    base = os.path.dirname(__file__)
    emp_path = os.path.join(base, "employees.parquet")
    mkt_path = os.path.join(base, "market.parquet")
    sti_path = os.path.join(base, "sti_targets.parquet")

    if not os.path.exists(emp_path):
        employees = generate_employees(500)
        market = generate_market_data()
        sti = generate_sti_targets()
        employees.to_parquet(emp_path, index=False)
        market.to_parquet(mkt_path, index=False)
        sti.to_parquet(sti_path, index=False)
    else:
        employees = pd.read_parquet(emp_path)
        market = pd.read_parquet(mkt_path)
        sti = pd.read_parquet(sti_path)

    return employees, market, sti


if __name__ == "__main__":
    emp, mkt, sti = load_or_generate()
    print(f"Employees: {len(emp)} rows")
    print(f"Market benchmarks: {len(mkt)} rows")
    print(f"STI targets: {len(sti)} rows")
    print(emp.head(3).to_string())
