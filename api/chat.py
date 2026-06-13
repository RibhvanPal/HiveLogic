from fastapi import APIRouter, HTTPException

from services.chat_service import (
    save_message,
    get_messages,
)
from services.session_service import (
    get_session,
)
from db.models import (
    SessionLocal,
    Report,
)
from agents.chat_agent import (
    chat_agent_node,
)
from rag.retriever import (
    retrieve_report_chunks,
)
router = APIRouter()

@router.post("/chat")
def chat(payload: dict):
    session_id = payload["session_id"]
    question = payload["message"]
    session = get_session(
        session_id
    )
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )
    db = SessionLocal()
    report = (
        db.query(Report)
        .filter(
            Report.id == session.report_id
        )
        .first()
    )
    db.close()

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )
    history = get_messages(
        session_id,
        limit=20,
    )
    history_text = "\n".join(
        [
            f"{m.role}: {m.content}"
            for m in history
        ]
    )
    retrieved_chunks = retrieve_report_chunks(
        report.id,
        question,
        k=5,
    )
    retrieved_text = "\n\n".join(
        [
            f"[{c['source']}]\n{c['text']}"
            for c in retrieved_chunks
        ]
    )

    report_context = f"""
    FINAL REPORT

    {report.final_report[:8000]}

    FINANCIAL METRICS

    {report.financial_metrics}

    CONTAGION RISKS

    {report.contagion_risks}

    CITATIONS

    {report.citations}

    RETRIEVED EVIDENCE

    {retrieved_text}
    """
    answer = chat_agent_node(
        report_context,
        history_text,
        question,
    )

    save_message(
        session_id,
        "user",
        question,
    )

    save_message(
        session_id,
        "assistant",
        answer,
    )

    return {
        "response": answer
    }