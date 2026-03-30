# CompIQ — AI Compensation Intelligence Platform

An AI-powered compensation analytics platform built to demonstrate the full scope of a Rewards Analyst role — market benchmarking, pay equity analysis, STI tooling, promotion modelling, and an AI Agent powered by GPT-4o.

> Built as a practical demonstration aligned with the Sasol Rewards Analyst role requirements.

---

## Features

| Module | Description |
|---|---|
| 📊 Dashboard | Overview of all compensation modules |
| 📈 Market Benchmarking | Compare internal salaries vs P25/P50/P75/P90 market data |
| ⚖️ Gender Pay Gap | Mean & median gap analysis with statistical significance testing |
| 💰 Salary Increase Simulator | Interactive merit matrix with budget utilisation tracking |
| 🚀 Promotion Calculator | Salary recommendations and cost impact for promotions |
| 🎯 STI Tool | Short-term incentive payout analysis with configurable multipliers |
| 🤖 AI Agent | GPT-4o powered agent — ask compensation questions in plain English |

---

## AI Agent

The AI Agent uses **GPT-4o with function calling** to query live compensation data and answer questions like:

- *"What is the gender pay gap in the Engineering department?"*
- *"Which employees in Germany are below market P25?"*
- *"How much will a 4% salary budget cost in the US?"*
- *"Recommend a salary for a Grade 5 Manager in the UK"*
- *"Which departments have the highest retention risk?"*

---

## Tech Stack

- **Frontend:** Streamlit
- **AI:** OpenAI GPT-4o (function calling) — also compatible with Anthropic Claude
- **Data:** Pandas, NumPy, SciPy, Plotly
- **Language:** Python 3.13

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/IshuDhana/compiq.git
cd compiq
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your_openai_key_here
```

### 5. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Data

The platform uses **synthetically generated employee data** (500 employees across Germany, USA, UK, Singapore, and South Africa) created using the Faker library. No real employee data is used.

---

## Project Structure

```
compiq/
├── app.py                  # Main Streamlit entry point
├── pages/                  # Individual page modules
│   ├── 1_Dashboard.py
│   ├── 2_Market_Benchmarking.py
│   ├── 3_Gender_Pay_Gap.py
│   ├── 4_Salary_Increase_Simulator.py
│   ├── 5_Promotion_Calculator.py
│   ├── 6_STI_Tool.py
│   └── 7_AI_Agent.py
├── modules/
│   └── ai_agent.py         # GPT-4o agent with function calling
├── utils/
│   └── compensation.py     # Compensation calculation utilities
├── data/
│   └── generate_data.py    # Synthetic data generation
└── requirements.txt
```

---

## Author

**Dhana** — [GitHub](https://github.com/IshuDhana)
