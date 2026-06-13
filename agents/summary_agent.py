import uuid
from datetime import datetime, UTC
from .state import HiveLogicState
from .llm_synthesis import call_llm

SUMMARY_SYSTEM = """
You are a senior financial research analyst.
Generate a professional research report using ONLY the supplied information.

Rules:
- Be factual and balanced.
- Do not provide buy, sell, hold, target price, or investment advice.
- Do not invent metrics, risks, news, or evidence.
- Mention uncertainty when data is limited.
- Use clean markdown formatting.

Required sections:
1. Executive Summary
2. Financial Overview
3. Market Sentiment
4. Key Risks
5. Contagion & Systemic Risks
6. Verification Summary
7. Conclusion
8. Disclaimer

End with:

DISCLAIMER: This is not financial advice.
For investment decisions, consult a SEBI/FINRA registered financial advisor.
"""

def format_metrics(metrics: dict) -> str:
    if not metrics or "error" in metrics:
        return "Financial metrics unavailable."

    field_map = {
        "market_cap_fmt": "Market Cap",
        "pe_ratio": "P/E Ratio",
        "forward_pe": "Forward P/E",
        "eps": "EPS (TTM)",
        "revenue": "Revenue",
        "profit_margin": "Profit Margin",
        "debt_to_equity": "Debt / Equity",
        "current_ratio": "Current Ratio",
        "beta": "Beta",
        "52w_high": "52 Week High",
        "52w_low": "52 Week Low",
        "current_price": "Current Price",
        "analyst_rating": "Analyst Rating",
    }

    rows = []
    for key, label in field_map.items():
        value = metrics.get(key)
        if value is None:
            continue
        if isinstance(value, float):
            rows.append(f"| {label} | {value:.2f} |")
        else:
            rows.append(f"| {label} | {value} |")
    if not rows:
        return "Financial metrics unavailable."
    return (
        "| Metric | Value |\n"
        "|--------|-------|\n"
        + "\n".join(rows)
    )

def summary_agent_node(state: HiveLogicState) -> HiveLogicState:
    ticker = state["company_ticker"]
    metrics = state.get("financial_metrics", {})
    company_name = metrics.get("company_name", ticker)

    print(f"[Summary Agent] Compiling report for {company_name}")
    news_headlines = "\n".join(
        f"- {article.get('title')}"
        for article in state.get("news_articles", [])[:5]
        if article.get("title")
    )
    contagion_risks = state.get("contagion_risks", [])
    if contagion_risks:
        contagion_text = "\n".join(
            [
                f"- {risk.get('severity','MEDIUM')} | "
                f"{risk.get('entity','Unknown')} | "
                f"{risk.get('relation','Unknown')} | "
                f"Risk Score: {risk.get('risk_weight',0):.0%} | "
                f"Path: {risk.get('path','')}"
                for risk in contagion_risks[:5]
            ]
        )
    else:
        contagion_text = "No contagion risks identified."
    verified_claims = state.get("verified_claims", [])
    verification_text = "\n".join(
        f"- {claim.get('claim')}"
        for claim in verified_claims[:5]
    )

    user_prompt = f"""
Company: {company_name} ({ticker})
Date: {datetime.now(UTC).strftime("%B %d, %Y")}

User Query:
{state.get("user_query", "")}

Financial Metrics:
{format_metrics(metrics)}

Sentiment:
Label: {state.get("sentiment_label", "Neutral")}
Score: {state.get("sentiment_score", 0.0):.2f}

Recent News:
{news_headlines or "No recent news available."}

Risk Analysis:
{state.get("risk_summary", "No risk analysis available.")}

Contagion Risks:
{contagion_text or "No contagion risks identified."}

Filing Context:
{state.get("filings_text", "")[:1000]}

Verification Status:
Verified = {state.get("verified", False)}

Verification Notes:
{state.get("verification_notes", "")}

Verified Claims:
{verification_text or "No verified claims available."}
"""

    report = call_llm(SUMMARY_SYSTEM, user_prompt)
    report_id = None
    try:
        from db.models import SessionLocal, Report, init_db
        init_db()

        db = SessionLocal()

        record = Report(
            id=str(uuid.uuid4()),

            ticker=ticker,

            query=state.get("user_query", ""),

            final_report=report,

            financial_metrics=state.get(
                "financial_metrics",
                {}
            ),

            contagion_risks=state.get(
                "contagion_risks",
                []
            ),

            sentiment_label=state.get(
                "sentiment_label"
            ),

            sentiment_score=state.get(
                "sentiment_score"
            ),

            verified=state.get(
                "verified",
                False
            ),

            citations=state.get(
                "citations",
                []
            ),
        )

        db.add(record)
        db.commit()

        report_id = record.id
        import os
        import shutil

        source_dir = "data/faiss_index"
        target_dir = f"data/vectorstores/{report_id}"

        if os.path.exists(source_dir):
            os.makedirs(
                "data/vectorstores",
                exist_ok=True,
            )
            shutil.copytree(
                source_dir,
                target_dir,
                dirs_exist_ok=True,
            )
            print(
                f"[Summary Agent] FAISS copied -> {target_dir}"
            )

        db.close()

        print(f"[Summary Agent] Report saved -> {report_id}")

    except Exception as e:
        print(f"[Summary Agent] DB save failed: {e}")

    return {
        **state,
        "final_report": report,
        "report_id": report_id,
    }