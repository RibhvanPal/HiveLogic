from langgraph.graph import StateGraph, END
from .state import HiveLogicState
from .filing_agent import filing_agent_node
from .news_agent import news_agent_node
from .metrics_agent import metrics_agent_node
from .sentiment_agent import sentiment_agent_node
from .risk_agent import risk_agent_node
from .verification_agent import verification_agent_node
from .citation_agent import citation_agent_node
from .summary_agent import summary_agent_node
from compliance.shield import check_compliance

def compliance_node(state: HiveLogicState) -> HiveLogicState:
    is_compliant, message = check_compliance(
        state["user_query"]
    )
    return {
        **state,
        "is_compliant": is_compliant,
        "compliance_message": message,
    }

def should_continue(state: HiveLogicState) -> str:
    if not state.get("is_compliant", True):
        return "blocked"
    return "proceed"

def build_pipeline():
    graph = StateGraph(HiveLogicState)

    graph.add_node("compliance", compliance_node)
    graph.add_node("filing", filing_agent_node)
    graph.add_node("metrics", metrics_agent_node)
    graph.add_node("news", news_agent_node)
    graph.add_node("sentiment", sentiment_agent_node)
    graph.add_node("risk", risk_agent_node)
    graph.add_node("verification", verification_agent_node)
    graph.add_node("summary", summary_agent_node)
    graph.add_node("citation", citation_agent_node)

    graph.set_entry_point("compliance")

    graph.add_conditional_edges(
        "compliance",
        should_continue,
        {
            "blocked": END,
            "proceed": "filing",
        },
    )

    graph.add_edge("filing", "metrics")
    graph.add_edge("metrics", "news")
    graph.add_edge("news", "sentiment")
    graph.add_edge("sentiment", "risk")
    graph.add_edge("risk", "verification")  # verify evidence
    graph.add_edge("verification", "citation") # build citations from verified evidence
    graph.add_edge("citation", "summary") # generate final report using citations & verification
    graph.add_edge("summary", END)

    return graph.compile()

_pipeline = None

def get_pipeline():
    global _pipeline

    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline

def run_pipeline(
    query: str,
    ticker: str,
    ) -> HiveLogicState:

    initial_state: HiveLogicState = {
        "user_query": query,
        "company_ticker": ticker.upper().strip(),

        "is_compliant": True,
        "compliance_message": "",

        "filings_text": "",
        "news_articles": [],
        "financial_metrics": {},

        "sentiment_score": 0.0,
        "sentiment_label": "Neutral",

        "risk_summary": "",
        "contagion_risks": [],

        "rag_chunks": [],

        "verified": False,
        "verification_notes": "",
        "verified_claims": [],

        "citations": [],

        "final_report": "",
        "report_id": None,

        "errors": [],
    }

    pipeline = get_pipeline()
    return pipeline.invoke(initial_state)