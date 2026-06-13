import uuid
from db.models import SessionLocal, Report
from db.chat_models import ChatSession

def create_session(report_id):
    db = SessionLocal()
    report = (
        db.query(Report)
        .filter(Report.id == report_id)
        .first()
    )
    if not report:
        db.close()
        raise ValueError(
            f"Report {report_id} not found"
        )

    session = ChatSession(
        id=str(uuid.uuid4()),
        report_id=report.id,
        ticker=report.ticker,
        title=f"{report.ticker} Chat",
    )
    db.add(session)
    db.commit()
    session_id = session.id
    db.close()
    return session_id

def get_sessions():
    db = SessionLocal()
    sessions = (
        db.query(ChatSession)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    db.close()
    return sessions


def get_session(session_id):
    db = SessionLocal()
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id
        )
        .first()
    )
    db.close()
    return session