import uuid
from db.models import SessionLocal
from db.chat_models import (
    ChatMessage,
)

def save_message(
    session_id,
    role,
    content,
):
    db = SessionLocal()
    msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=role,
        content=content,
    )
    db.add(msg)
    db.commit()
    db.close()


def get_messages(
    session_id,
    limit=20,
):
    db = SessionLocal()
    msgs = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id
        )
        .order_by(
            ChatMessage.created_at.desc()
        )
        .limit(limit)
        .all()
    )
    db.close()
    return list(reversed(msgs))