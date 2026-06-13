from .state import HiveLogicState
from .llm_synthesis import call_llm
from graph.contagion import summarize_contagion

RISK_SYSTEM = """
You are a financial risk analyst.

Analyze the company using:
- Financial metrics
- Filing information
- Market sentiment
- Contagion risks

Focus on:
1. Financial risks
2. Market risks
3. Regulatory risks
4. Operational risks
5. Supply-chain or contagion risks

Rules:
- Be factual and concise.
- Do not provide buy/sell recommendations.
- Do not invent information not present in the input.
- Mention sentiment only if it materially affects risk.
- Only discuss risks explicitly present in the provided data.
- Do not infer new business dependencies.
- Do not convert graph relationships into factual company statements unless directly supported by filings or metrics.
- If a risk comes from the contagion graph, explicitly label it as a graph-derived risk.
- Do not present graph-derived risks as confirmed company disclosures.
- Do not infer risks from neutral sentiment.
- Do not invent operational risks.

CRITICAL:

Every bullet must be directly traceable
to ONE of:

1. financial metrics
2. filing text
3. contagion graph
4. sentiment score

If evidence is missing,
DO NOT mention the risk.

Do not infer product dependencies.

Do not infer market position.

Do not infer business model risks.

Do not infer concentration risks.

Do not invent operational risks.


Output 3-5 markdown bullet points.
"""


def risk_agent_node(state: HiveLogicState) -> HiveLogicState:
    ticker = state["company_ticker"]

    print(f"[Risk Agent] Analyzing risks for {ticker}")

    contagion = summarize_contagion(ticker)
    metrics = state.get("financial_metrics", {})
    filings = state.get("filings_text", "")[:1500]
    sentiment_label = state.get("sentiment_label", "Neutral")
    sentiment_score = state.get("sentiment_score", 0.0)

    metrics_str = "\n".join(
        f"{k}: {v}"
        for k, v in metrics.items()
        if v is not None and k not in {"description", "error"}
    )

    if contagion:
        contagion_text = "\n".join(
            [
                f"{r['severity']} | "
                f"{r['entity']} | "
                f"{r['relation']} | "
                f"{r['risk_weight']:.0%} | "
                f"{r['path']}"
                for r in contagion
            ]
        )
    else:
        contagion_text = "No contagion risks identified."

    user_prompt = (
        f"Company: {metrics.get('company_name', ticker)} ({ticker})\n\n"
        f"Financial Metrics:\n{metrics_str}\n\n"
        f"Market Sentiment:\n"
        f"Label: {sentiment_label}\n"
        f"Score: {sentiment_score:.2f}\n\n"
        f"Filing Context:\n{filings}\n\n"
        f"Contagion Risks:\n{contagion_text}"
    )
    risk_summary = call_llm(RISK_SYSTEM, user_prompt)

    return {
        **state,
        "risk_summary": risk_summary,
        "contagion_risks": contagion,
    }