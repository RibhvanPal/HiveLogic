from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.session_service import (
    create_session,
    get_sessions,
)

router = APIRouter(
    prefix="/api",
    tags=["chat"]
)

class SessionRequest(BaseModel):
    report_id: str

@router.post("/sessions")
def new_session(payload: SessionRequest):
    try:
        session_id = create_session(
            payload.report_id
        )
        return {
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

@router.get("/sessions")
def list_sessions():
    sessions = get_sessions()
    return [
        {
            "id": s.id,
            "title": s.title,
            "ticker": s.ticker,
            "report_id": s.report_id,
            "created_at": s.created_at,
        }
        for s in sessions
    ]