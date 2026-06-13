from __future__ import annotations

import json
from datetime import date, timedelta
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


APP_NAME = "MoneyMap"
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "moneymap_data.json"
CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Other"]
ASSET_TYPES = ["Stock", "ETF", "Crypto", "Bond", "Fund", "Cash", "Other"]


DEFAULT_DATA: dict[str, Any] = {
    "transactions": [],
    "budgets": {category: 0.0 for category in CATEGORIES},
    "goals": [],
    "investments": [],
}


DEMO_DATA: dict[str, Any] = {
    "transactions": [
        {"id": 1, "date": "2026-06-01", "type": "Income", "category": "Other", "description": "Salary", "amount": 4200.0},
        {"id": 2, "date": "2026-06-03", "type": "Expense", "category": "Bills", "description": "Rent", "amount": 1450.0},
        {"id": 3, "date": "2026-06-04", "type": "Expense", "category": "Food", "description": "Groceries", "amount": 186.35},
        {"id": 4, "date": "2026-06-06", "type": "Expense", "category": "Transport", "description": "Transit pass", "amount": 54.0},
        {"id": 5, "date": "2026-06-08", "type": "Expense", "category": "Entertainment", "description": "Concert tickets", "amount": 120.0},
        {"id": 6, "date": "2026-06-11", "type": "Expense", "category": "Shopping", "description": "New headphones", "amount": 89.99},
        {"id": 7, "date": "2026-05-01", "type": "Income", "category": "Other", "description": "Salary", "amount": 4200.0},
        {"id": 8, "date": "2026-05-04", "type": "Expense", "category": "Bills", "description": "Rent", "amount": 1450.0},
        {"id": 9, "date": "2026-05-09", "type": "Expense", "category": "Food", "description": "Restaurants", "amount": 255.7},
        {"id": 10, "date": "2026-04-01", "type": "Income", "category": "Other", "description": "Salary", "amount": 4100.0},
        {"id": 11, "date": "2026-04-07", "type": "Expense", "category": "Bills", "description": "Utilities", "amount": 212.25},
        {"id": 12, "date": "2026-04-13", "type": "Expense", "category": "Food", "description": "Meal prep", "amount": 170.15},
    ],
    "budgets": {
        "Food": 500.0,
        "Transport": 160.0,
        "Entertainment": 250.0,
        "Shopping": 300.0,
        "Bills": 1800.0,
        "Other": 200.0,
    },
    "goals": [
        {"id": 1, "name": "Emergency fund", "target": 10000.0, "current": 6200.0, "created_at": "2026-01-01", "target_date": "2026-12-31"},
        {"id": 2, "name": "Japan trip", "target": 4500.0, "current": 1850.0, "created_at": "2026-01-01", "target_date": "2026-09-30"},
        {"id": 3, "name": "New laptop", "target": 2200.0, "current": 900.0, "created_at": "2026-03-01", "target_date": "2026-08-31"},
    ],
    "investments": [
        {"id": 1, "asset": "S&P 500 ETF", "type": "ETF", "amount_invested": 8500.0, "current_value": 9725.0},
        {"id": 2, "asset": "Global Bond Fund", "type": "Bond", "amount_invested": 3500.0, "current_value": 3420.0},
        {"id": 3, "asset": "Tech Growth Stock", "type": "Stock", "amount_invested": 2400.0, "current_value": 2880.0},
    ],
}


st.set_page_config(
    page_title=APP_NAME,
    page_icon="$",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_data() -> dict[str, Any]:
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        save_data(DEFAULT_DATA.copy())
    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return {**DEFAULT_DATA, **data}


def save_data(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def next_id(items: list[dict[str, Any]]) -> int:
    return max((int(item.get("id", 0)) for item in items), default=0) + 1


def money(value: float) -> str:
    return f"${value:,.2f}"


def transactions_df(data: dict[str, Any]) -> pd.DataFrame:
    df = pd.DataFrame(data["transactions"])
    if df.empty:
        return pd.DataFrame(columns=["id", "date", "type", "category", "description", "amount", "month"])
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df.sort_values("date", ascending=False)


def goals_df(data: dict[str, Any]) -> pd.DataFrame:
    df = pd.DataFrame(data["goals"])
    if df.empty:
        return pd.DataFrame(columns=["id", "name", "target", "current", "progress"])
    df["progress"] = df.apply(lambda row: min(float(row["current"]) / float(row["target"]), 1.0) if float(row["target"]) else 0.0, axis=1)
    return df


def investments_df(data: dict[str, Any]) -> pd.DataFrame:
    df = pd.DataFrame(data["investments"])
    if df.empty:
        return pd.DataFrame(columns=["id", "asset", "type", "amount_invested", "current_value", "profit_loss", "return_pct"])
    df["profit_loss"] = df["current_value"] - df["amount_invested"]
    df["return_pct"] = df.apply(
        lambda row: (float(row["profit_loss"]) / float(row["amount_invested"]) * 100) if float(row["amount_invested"]) else 0.0,
        axis=1,
    )
    return df


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #0c111d;
            --panel: #111827;
            --panel-soft: #172033;
            --text: #eef4ff;
            --muted: #94a3b8;
            --green: #35d399;
            --red: #fb7185;
            --blue: #38bdf8;
            --amber: #fbbf24;
        }
        .stApp {
            background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.12), transparent 32%),
                        linear-gradient(135deg, #080c15 0%, #111827 50%, #0c111d 100%);
            color: var(--text);
        }
        [data-testid="stSidebar"] {
            background: rgba(8, 12, 21, 0.92);
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        .hero {
            padding: 1.2rem 0 1.1rem;
        }
        .hero h1 {
            font-size: 2.8rem;
            margin: 0;
        }
        .hero p {
            color: var(--muted);
            font-size: 1.02rem;
            margin-top: .35rem;
        }
        .metric-card {
            background: linear-gradient(145deg, rgba(17, 24, 39, .96), rgba(23, 32, 51, .96));
            border: 1px solid rgba(148, 163, 184, .18);
            border-radius: 8px;
            padding: 1rem;
            min-height: 124px;
            box-shadow: 0 16px 36px rgba(0, 0, 0, .22);
        }
        .metric-label {
            color: var(--muted);
            font-size: .84rem;
            text-transform: uppercase;
            letter-spacing: .08rem;
        }
        .metric-value {
            font-size: 1.9rem;
            font-weight: 750;
            margin-top: .4rem;
            color: var(--text);
        }
        .metric-help {
            color: var(--muted);
            font-size: .86rem;
            margin-top: .35rem;
        }
        .panel {
            background: rgba(17, 24, 39, .82);
            border: 1px solid rgba(148, 163, 184, .16);
            border-radius: 8px;
            padding: 1rem;
        }
        .empty-state {
            border: 1px dashed rgba(148, 163, 184, .38);
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            color: var(--muted);
            background: rgba(17, 24, 39, .45);
        }
        .success-text { color: var(--green); font-weight: 700; }
        .danger-text { color: var(--red); font-weight: 700; }
        .warning-box {
            border-left: 4px solid var(--amber);
            background: rgba(251, 191, 36, .1);
            padding: .8rem 1rem;
            border-radius: 8px;
        }
        .insight-card {
            position: relative;
            min-height: 184px;
            height: 100%;
            background:
                linear-gradient(145deg, rgba(17, 24, 39, .96), rgba(23, 32, 51, .9));
            border: 1px solid rgba(148, 163, 184, .16);
            border-left: 4px solid var(--blue);
            border-radius: 8px;
            padding: 1.05rem;
            box-shadow: 0 14px 30px rgba(0, 0, 0, .18);
            overflow: hidden;
            animation: insightFadeIn .42s ease both;
            transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease, background .18s ease;
        }
        .insight-card:hover {
            transform: translateY(-3px);
            border-color: rgba(148, 163, 184, .32);
            box-shadow: 0 20px 42px rgba(0, 0, 0, .28);
        }
        .insight-card.recommendation {
            border-left-color: var(--green);
            background:
                linear-gradient(145deg, rgba(16, 43, 38, .7), rgba(17, 24, 39, .95));
        }
        .insight-card.warning {
            border-left-color: var(--amber);
            background:
                linear-gradient(145deg, rgba(47, 34, 14, .78), rgba(17, 24, 39, .95));
        }
        .insight-topline {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: .75rem;
        }
        .insight-icon {
            width: 2.25rem;
            height: 2.25rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            color: #bae6fd;
            background: rgba(56, 189, 248, .13);
            border: 1px solid rgba(56, 189, 248, .22);
            flex: 0 0 auto;
        }
        .insight-card.recommendation .insight-icon {
            color: #a7f3d0;
            background: rgba(53, 211, 153, .13);
            border-color: rgba(53, 211, 153, .24);
        }
        .insight-card.warning .insight-icon {
            color: #fde68a;
            background: rgba(251, 191, 36, .14);
            border-color: rgba(251, 191, 36, .24);
        }
        .insight-icon svg {
            width: 1.1rem;
            height: 1.1rem;
            stroke-width: 2.1;
        }
        .severity-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: .24rem .62rem;
            color: #dbeafe;
            background: rgba(56, 189, 248, .14);
            font-size: .72rem;
            font-weight: 750;
            letter-spacing: .04rem;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .insight-card.recommendation .severity-badge {
            color: #d1fae5;
            background: rgba(53, 211, 153, .14);
        }
        .insight-card.warning .severity-badge {
            color: #fef3c7;
            background: rgba(251, 191, 36, .16);
        }
        .insight-title {
            margin-top: 1rem;
            font-size: 1.06rem;
            font-weight: 750;
            color: var(--text);
            line-height: 1.25;
        }
        .insight-body {
            margin-top: .4rem;
            color: var(--muted);
            font-size: .92rem;
            line-height: 1.45;
        }
        .insight-action {
            margin-top: .8rem;
            color: var(--text);
            font-size: .88rem;
            font-weight: 650;
        }
        .insights-intro {
            color: var(--muted);
            margin: -.25rem 0 1rem;
            max-width: 720px;
        }
        .insights-empty {
            border: 1px dashed rgba(56, 189, 248, .34);
            border-radius: 8px;
            padding: 1.4rem;
            background:
                linear-gradient(145deg, rgba(17, 24, 39, .76), rgba(23, 32, 51, .58));
            color: var(--muted);
        }
        .insights-empty-title {
            color: var(--text);
            font-size: 1.05rem;
            font-weight: 750;
            margin-bottom: .35rem;
        }
        @keyframes insightFadeIn {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .stProgress > div > div > div > div {
            background-image: linear-gradient(90deg, #38bdf8, #35d399);
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(148, 163, 184, .16);
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, help_text: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <h3>{title}</h3>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_icon(severity: str) -> str:
    icons = {
        "Info": """
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
            <circle cx="12" cy="12" r="9"></circle>
            <path d="M12 10v6"></path>
            <path d="M12 7h.01"></path>
        </svg>
        """,
        "Recommendation": """
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
            <path d="M12 3l1.7 4.7L18 10l-4.3 2.3L12 17l-1.7-4.7L6 10l4.3-2.3L12 3z"></path>
            <path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z"></path>
        </svg>
        """,
        "Warning": """
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
            <path d="M10.3 4.3L2.7 18a2 2 0 0 0 1.8 3h15a2 2 0 0 0 1.8-3L13.7 4.3a2 2 0 0 0-3.4 0z"></path>
            <path d="M12 9v4"></path>
            <path d="M12 17h.01"></path>
        </svg>
        """,
    }
    return icons.get(severity, icons["Info"])


def insight_card(severity: str, title: str, body: str, action: str, index: int) -> str:
    severity_class = severity.lower()
    return f"""
    <div class="insight-card {severity_class}" style="animation-delay: {min(index * 0.05, 0.35):.2f}s;">
        <div class="insight-topline">
            <div class="insight-icon">{insight_icon(severity)}</div>
            <div class="severity-badge">{escape(severity)}</div>
        </div>
        <div class="insight-title">{escape(title)}</div>
        <div class="insight-body">{escape(body)}</div>
        <div class="insight-action">{escape(action)}</div>
    </div>
    """


def render_insights(insights: list[dict[str, str]]) -> None:
    st.subheader("Insights Center")
    st.markdown(
        '<p class="insights-intro">Rule-based recommendations based on your budgets, cash flow, goals, and portfolio mix.</p>',
        unsafe_allow_html=True,
    )
    if not insights:
        st.markdown(
            """
            <div class="insights-empty">
                <div class="insights-empty-title">No insights yet</div>
                <div>Add transactions, budgets, savings goals, or investments to unlock personalized rule-based recommendations.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for start in range(0, len(insights), 3):
        columns = st.columns(3)
        for offset, insight in enumerate(insights[start : start + 3]):
            with columns[offset]:
                st.markdown(
                    insight_card(insight["severity"], insight["title"], insight["body"], insight["action"], start + offset),
                    unsafe_allow_html=True,
                )


def current_month_summary(df: pd.DataFrame) -> dict[str, float]:
    this_month = date.today().strftime("%Y-%m")
    month_df = df[df["month"] == this_month] if not df.empty else df
    income = month_df.loc[month_df["type"] == "Income", "amount"].sum() if not month_df.empty else 0.0
    expenses = month_df.loc[month_df["type"] == "Expense", "amount"].sum() if not month_df.empty else 0.0
    savings = income - expenses
    savings_rate = (savings / income * 100) if income else 0.0
    return {"income": income, "expenses": expenses, "savings": savings, "savings_rate": savings_rate}


def generate_insights(data: dict[str, Any], tx: pd.DataFrame, goals: pd.DataFrame, inv: pd.DataFrame, total_cash: float) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []
    summary = current_month_summary(tx)
    this_month = date.today().strftime("%Y-%m")
    monthly_expenses = summary["expenses"]
    monthly_income = summary["income"]

    if tx.empty and goals.empty and inv.empty and all(float(value) == 0 for value in data["budgets"].values()):
        return []

    if tx.empty:
        insights.append(
            {
                "severity": "Info",
                "title": "Start with transaction history",
                "body": "MoneyMap can generate sharper recommendations once income and expenses are logged.",
                "action": "Add transactions or load demo data from the sidebar.",
            }
        )

    if monthly_income > 0:
        if summary["savings_rate"] < 0:
            insights.append(
                {
                    "severity": "Warning",
                    "title": "Monthly spending is above income",
                    "body": f"Your current savings rate is {summary['savings_rate']:.1f}%, which means expenses exceed income this month.",
                    "action": "Review flexible categories and pause non-essential purchases.",
                }
            )
        elif summary["savings_rate"] < 20:
            insights.append(
                {
                    "severity": "Recommendation",
                    "title": "Savings rate is below 20%",
                    "body": f"You are saving {summary['savings_rate']:.1f}% of income this month. A 20% target would improve long-term resilience.",
                    "action": "Try moving a small amount to savings right after income arrives.",
                }
            )

    current_expenses = tx[(tx["type"] == "Expense") & (tx["month"] == this_month)] if not tx.empty else tx
    if not current_expenses.empty and monthly_expenses > 0:
        category_spend = current_expenses.groupby("category")["amount"].sum()
        food_spend = float(category_spend.get("Food", 0.0))
        food_share = food_spend / monthly_expenses
        if food_share > 0.3:
            insights.append(
                {
                    "severity": "Recommendation",
                    "title": "Food spending is running high",
                    "body": f"Food is {food_share * 100:.1f}% of this month's expenses, above the 30% guideline.",
                    "action": "Set a weekly food cap or split groceries from restaurants.",
                }
            )

        for category, budget in data["budgets"].items():
            budget_amount = float(budget)
            spent = float(category_spend.get(category, 0.0))
            if budget_amount > 0 and spent > budget_amount:
                insights.append(
                    {
                        "severity": "Warning",
                        "title": f"{category} is over budget",
                        "body": f"You have spent {money(spent)} against a {money(budget_amount)} monthly budget.",
                        "action": f"Reduce {category.lower()} spending by {money(spent - budget_amount)} to get back on plan.",
                    }
                )

    if monthly_income > 0 and total_cash > max(monthly_expenses * 3, monthly_income) and summary["savings_rate"] >= 25:
        insights.append(
            {
                "severity": "Info",
                "title": "Cash balance is growing quickly",
                "body": f"Your cash balance is {money(total_cash)} and this month's savings rate is {summary['savings_rate']:.1f}%.",
                "action": "Consider allocating surplus cash to savings goals or diversified investments.",
            }
        )

    today = date.today()
    if not goals.empty:
        for _, goal in goals.iterrows():
            target_date_raw = goal.get("target_date")
            created_at_raw = goal.get("created_at")
            if not target_date_raw or not created_at_raw:
                continue
            target_date = pd.to_datetime(target_date_raw).date()
            created_at = pd.to_datetime(created_at_raw).date()
            total_days = max((target_date - created_at).days, 1)
            elapsed_days = min(max((today - created_at).days, 0), total_days)
            expected_progress = elapsed_days / total_days
            actual_progress = float(goal["progress"])
            if target_date >= today and actual_progress + 0.08 < expected_progress and actual_progress < 1:
                insights.append(
                    {
                        "severity": "Recommendation",
                        "title": f"{goal['name']} is behind schedule",
                        "body": f"This goal is {actual_progress * 100:.1f}% funded, while the timeline suggests about {expected_progress * 100:.1f}%.",
                        "action": "Increase contributions or adjust the target date.",
                    }
                )

    if not inv.empty:
        total_portfolio = float(inv["current_value"].sum())
        if total_portfolio > 0:
            top_asset = inv.sort_values("current_value", ascending=False).iloc[0]
            concentration = float(top_asset["current_value"]) / total_portfolio
            if concentration > 0.5:
                insights.append(
                    {
                        "severity": "Warning",
                        "title": "Portfolio concentration is high",
                        "body": f"{top_asset['asset']} represents {concentration * 100:.1f}% of your tracked portfolio.",
                        "action": "Consider diversifying across asset types or positions.",
                    }
                )

    if not insights and (monthly_income > 0 or not inv.empty or not goals.empty):
        insights.append(
            {
                "severity": "Info",
                "title": "Finances look balanced",
                "body": "No major rule-based warnings were detected from the current data.",
                "action": "Keep tracking consistently to make trends more reliable.",
            }
        )

    severity_rank = {"Warning": 0, "Recommendation": 1, "Info": 2}
    insights.sort(key=lambda item: severity_rank.get(item["severity"], 3))
    return insights


def page_dashboard(data: dict[str, Any]) -> None:
    tx = transactions_df(data)
    inv = investments_df(data)
    goals = goals_df(data)
    summary = current_month_summary(tx)

    total_cash = tx.loc[tx["type"] == "Income", "amount"].sum() - tx.loc[tx["type"] == "Expense", "amount"].sum() if not tx.empty else 0.0
    portfolio_value = inv["current_value"].sum() if not inv.empty else 0.0
    goal_savings = goals["current"].sum() if not goals.empty else 0.0
    net_worth = total_cash + portfolio_value + goal_savings

    st.markdown('<div class="hero"><h1>MoneyMap</h1><p>Your personal map for spending, saving, budgeting, and building wealth.</p></div>', unsafe_allow_html=True)

    cols = st.columns(5)
    with cols[0]:
        metric_card("Total Balance", money(total_cash), "Income minus expenses")
    with cols[1]:
        metric_card("Monthly Income", money(summary["income"]), date.today().strftime("%B %Y"))
    with cols[2]:
        metric_card("Monthly Expenses", money(summary["expenses"]), "Tracked spending")
    with cols[3]:
        metric_card("Savings Rate", f"{summary['savings_rate']:.1f}%", "Current month")
    with cols[4]:
        metric_card("Net Worth", money(net_worth), "Cash, goals, investments")

    st.write("")
    render_insights(generate_insights(data, tx, goals, inv, total_cash))

    st.write("")
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Monthly Cash Flow")
        if tx.empty:
            empty_state("No cash flow yet", "Add income and expenses or load demo data to see your monthly trend.")
        else:
            monthly = tx.groupby(["month", "type"], as_index=False)["amount"].sum()
            fig = px.bar(monthly, x="month", y="amount", color="type", barmode="group", color_discrete_map={"Income": "#35d399", "Expense": "#fb7185"})
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Portfolio Snapshot")
        if inv.empty:
            empty_state("No investments yet", "Track assets manually to estimate portfolio value and returns.")
        else:
            total_invested = inv["amount_invested"].sum()
            current_value = inv["current_value"].sum()
            profit_loss = current_value - total_invested
            st.metric("Current value", money(current_value), f"{profit_loss:+,.2f}")
            st.progress(min(max(current_value / max(total_invested, 1), 0), 1))
            st.caption(f"Invested: {money(total_invested)}")


def page_transactions(data: dict[str, Any]) -> None:
    st.title("Expense Tracking")
    st.caption("Log income and expenses, then review your transaction history.")

    with st.form("transaction_form", clear_on_submit=True):
        cols = st.columns([1, 1, 1])
        entry_date = cols[0].date_input("Date", value=date.today())
        entry_type = cols[1].selectbox("Type", ["Expense", "Income"])
        category = cols[2].selectbox("Category", CATEGORIES)
        description = st.text_input("Description", placeholder="Groceries, salary, rent...")
        amount = st.number_input("Amount", min_value=0.0, step=10.0, format="%.2f")
        submitted = st.form_submit_button("Add transaction", use_container_width=True)

    if submitted:
        if amount <= 0:
            st.warning("Enter an amount greater than zero.")
        else:
            data["transactions"].append(
                {
                    "id": next_id(data["transactions"]),
                    "date": entry_date.isoformat(),
                    "type": entry_type,
                    "category": category,
                    "description": description or category,
                    "amount": float(amount),
                }
            )
            save_data(data)
            st.success("Transaction added.")
            st.rerun()

    tx = transactions_df(data)
    st.subheader("Transaction History")
    if tx.empty:
        empty_state("Your ledger is waiting", "Add your first transaction to start building a clearer financial picture.")
    else:
        display = tx[["date", "type", "category", "description", "amount"]].copy()
        display["date"] = display["date"].dt.strftime("%Y-%m-%d")
        display["amount"] = display["amount"].map(money)
        st.dataframe(display, use_container_width=True, hide_index=True)


def page_budgeting(data: dict[str, Any]) -> None:
    st.title("Budgeting")
    st.caption("Set monthly category budgets and monitor your current spending pace.")

    with st.form("budget_form"):
        cols = st.columns(3)
        updated = {}
        for index, category in enumerate(CATEGORIES):
            with cols[index % 3]:
                updated[category] = st.number_input(f"{category} budget", min_value=0.0, value=float(data["budgets"].get(category, 0.0)), step=25.0)
        saved = st.form_submit_button("Save budgets", use_container_width=True)

    if saved:
        data["budgets"] = updated
        save_data(data)
        st.success("Budgets saved.")
        st.rerun()

    tx = transactions_df(data)
    this_month = date.today().strftime("%Y-%m")
    expenses = tx[(tx["type"] == "Expense") & (tx["month"] == this_month)] if not tx.empty else tx
    spent_by_category = expenses.groupby("category")["amount"].sum().to_dict() if not expenses.empty else {}

    st.subheader("Budget Usage")
    if all(float(value) == 0 for value in data["budgets"].values()):
        empty_state("No budgets set", "Add monthly budget amounts to turn spending into a plan.")
        return

    for category in CATEGORIES:
        budget = float(data["budgets"].get(category, 0.0))
        spent = float(spent_by_category.get(category, 0.0))
        ratio = spent / budget if budget else 0.0
        st.markdown(f"**{category}**")
        st.progress(min(ratio, 1.0))
        col_a, col_b = st.columns([1, 1])
        col_a.caption(f"Spent {money(spent)} of {money(budget)}")
        col_b.caption(f"{ratio * 100:.1f}% used")
        if budget and ratio > 1:
            st.markdown(f'<div class="warning-box">Overspending alert: {category} is {money(spent - budget)} over budget.</div>', unsafe_allow_html=True)


def page_goals(data: dict[str, Any]) -> None:
    st.title("Savings Goals")
    st.caption("Create goals and track progress toward the big things.")

    with st.form("goal_form", clear_on_submit=True):
        name = st.text_input("Goal name", placeholder="Emergency fund")
        cols = st.columns(3)
        target = cols[0].number_input("Target amount", min_value=0.0, step=100.0, format="%.2f")
        current = cols[1].number_input("Current savings", min_value=0.0, step=100.0, format="%.2f")
        target_date = cols[2].date_input("Target date", value=date.today() + timedelta(days=365))
        submitted = st.form_submit_button("Create goal", use_container_width=True)

    if submitted:
        if not name or target <= 0:
            st.warning("Add a goal name and a target amount greater than zero.")
        else:
            data["goals"].append(
                {
                    "id": next_id(data["goals"]),
                    "name": name,
                    "target": float(target),
                    "current": float(current),
                    "created_at": date.today().isoformat(),
                    "target_date": target_date.isoformat(),
                }
            )
            save_data(data)
            st.success("Goal created.")
            st.rerun()

    goals = goals_df(data)
    if goals.empty:
        empty_state("No goals yet", "Create a goal to make savings progress visible and motivating.")
        return

    for _, goal in goals.iterrows():
        st.markdown(f"### {goal['name']}")
        st.progress(float(goal["progress"]))
        cols = st.columns(3)
        cols[0].metric("Saved", money(float(goal["current"])))
        cols[1].metric("Target", money(float(goal["target"])))
        cols[2].metric("Complete", f"{float(goal['progress']) * 100:.1f}%")


def page_investments(data: dict[str, Any]) -> None:
    st.title("Investment Tracking")
    st.caption("Track manually entered assets and understand portfolio performance.")

    with st.form("investment_form", clear_on_submit=True):
        cols = st.columns([1.3, 1])
        asset = cols[0].text_input("Asset name", placeholder="S&P 500 ETF")
        asset_type = cols[1].selectbox("Asset type", ASSET_TYPES)
        cols = st.columns(2)
        invested = cols[0].number_input("Amount invested", min_value=0.0, step=100.0, format="%.2f")
        current = cols[1].number_input("Current value", min_value=0.0, step=100.0, format="%.2f")
        submitted = st.form_submit_button("Add investment", use_container_width=True)

    if submitted:
        if not asset or invested <= 0:
            st.warning("Add an asset name and invested amount greater than zero.")
        else:
            data["investments"].append(
                {
                    "id": next_id(data["investments"]),
                    "asset": asset,
                    "type": asset_type,
                    "amount_invested": float(invested),
                    "current_value": float(current),
                }
            )
            save_data(data)
            st.success("Investment added.")
            st.rerun()

    inv = investments_df(data)
    if inv.empty:
        empty_state("No investments tracked", "Add an asset to calculate portfolio value, gains, and losses.")
        return

    total_invested = inv["amount_invested"].sum()
    current_value = inv["current_value"].sum()
    profit_loss = current_value - total_invested
    cols = st.columns(3)
    cols[0].metric("Invested", money(total_invested))
    cols[1].metric("Current value", money(current_value))
    cols[2].metric("Profit / loss", money(profit_loss), f"{(profit_loss / total_invested * 100 if total_invested else 0):.1f}%")

    display = inv[["asset", "type", "amount_invested", "current_value", "profit_loss", "return_pct"]].copy()
    for column in ["amount_invested", "current_value", "profit_loss"]:
        display[column] = display[column].map(money)
    display["return_pct"] = display["return_pct"].map(lambda value: f"{value:.1f}%")
    st.dataframe(display, use_container_width=True, hide_index=True)


def page_analytics(data: dict[str, Any]) -> None:
    st.title("Analytics")
    st.caption("Explore spending patterns, cash flow, and savings momentum.")

    tx = transactions_df(data)
    goals = goals_df(data)
    if tx.empty:
        empty_state("Analytics need activity", "Add transactions or load demo data to unlock charts.")
        return

    col_a, col_b = st.columns(2)
    expenses = tx[tx["type"] == "Expense"]
    with col_a:
        st.subheader("Spending by Category")
        if expenses.empty:
            empty_state("No expenses yet", "Expense categories will appear here once you add spending.")
        else:
            category_spend = expenses.groupby("category", as_index=False)["amount"].sum()
            fig = px.pie(category_spend, names="category", values="amount", hole=0.55, color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Monthly Cash Flow")
        monthly = tx.groupby(["month", "type"], as_index=False)["amount"].sum()
        fig = px.line(monthly, x="month", y="amount", color="type", markers=True, color_discrete_map={"Income": "#35d399", "Expense": "#fb7185"})
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Savings Trends")
    monthly_pivot = tx.pivot_table(index="month", columns="type", values="amount", aggfunc="sum").fillna(0)
    monthly_pivot["Savings"] = monthly_pivot.get("Income", 0) - monthly_pivot.get("Expense", 0)
    savings = monthly_pivot.reset_index()
    fig = px.area(savings, x="month", y="Savings", color_discrete_sequence=["#38bdf8"])
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)

    if not goals.empty:
        st.subheader("Goal Completion")
        goal_chart = goals.copy()
        goal_chart["completed"] = goal_chart["progress"] * 100
        fig = px.bar(goal_chart, x="name", y="completed", color="completed", color_continuous_scale=["#38bdf8", "#35d399"])
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=20, b=10), yaxis_title="Completed %")
        st.plotly_chart(fig, use_container_width=True)


def sidebar(data: dict[str, Any]) -> str:
    st.sidebar.title("MoneyMap")
    st.sidebar.caption("Personal finance dashboard")
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Expense Tracking", "Budgeting", "Savings Goals", "Investment Tracking", "Analytics"],
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    if st.sidebar.button("Load demo data", use_container_width=True):
        save_data(json.loads(json.dumps(DEMO_DATA)))
        st.sidebar.success("Demo data loaded.")
        st.rerun()

    if st.sidebar.button("Reset all data", use_container_width=True):
        save_data(json.loads(json.dumps(DEFAULT_DATA)))
        st.sidebar.warning("Data reset.")
        st.rerun()

    st.sidebar.divider()
    tx = transactions_df(data)
    summary = current_month_summary(tx)
    st.sidebar.metric("This month's savings", money(summary["savings"]))
    return page


def main() -> None:
    inject_css()
    data = load_data()
    page = sidebar(data)

    if page == "Dashboard":
        page_dashboard(data)
    elif page == "Expense Tracking":
        page_transactions(data)
    elif page == "Budgeting":
        page_budgeting(data)
    elif page == "Savings Goals":
        page_goals(data)
    elif page == "Investment Tracking":
        page_investments(data)
    elif page == "Analytics":
        page_analytics(data)


if __name__ == "__main__":
    main()
