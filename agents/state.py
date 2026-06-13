from typing import TypedDict, Optional, List, Dict, Any
from typing import TypedDict, Optional, List, Dict

class HiveLogicState(TypedDict):
    # Input
    user_query: str
    company_ticker: str

    # Compliance
    is_compliant: bool
    compliance_message: str

    # Data
    filings_text: str
    news_articles: List[Dict]
    financial_metrics: Dict

    # Analysis
    sentiment_score: float
    sentiment_label: str
    risk_summary: str
    contagion_risks: List[Dict]

    # RAG
    rag_chunks: List[Dict]

    # Verification
    verified: bool
    verification_notes: str
    verified_claims: List[Dict]

    # Citations
    citations: List[Dict]

    # Output
    final_report: str
    report_id: Optional[str]

    # Errors
    errors: List[str]