import sys
import os
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from agents.orchestrator import run_pipeline
from db.models import init_db, get_db, Report, Watchlist

app = FastAPI(
    title="HiveLogic API",
    description="Multi-Agent Financial Research System",
    version="2.0.0",
)
try:
    from api.sessions import router as session_router
    from api.chat import router as chat_router

    app.include_router(session_router)
    app.include_router(chat_router)

except Exception as e:
    print(f"Chat routes not loaded: {e}")


init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173",],
    allow_methods=["*"],
    allow_headers=["*"],
)

class WatchlistRequest(BaseModel):
    ticker: str
    notes: Optional[str] = ""


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"
    return {
        "status": "ok",
        "service": "HiveLogic",
        "version": "2.0.0",
        "database": db_status,
    }

#Core Analysis
@app.post("/analyze")
async def analyze(
    ticker: str = Form(...),
    query: str = Form(...),
    pdf_file: Optional[UploadFile] = File(None),
):
    if not ticker.strip():
        raise HTTPException(400, "Ticker cannot be empty.")

    if not query.strip():
        raise HTTPException(400, "Query cannot be empty.")

    FAISS_PATH = os.getenv(
        "FAISS_INDEX_PATH",
        "data/faiss_index"
    )

    if os.path.exists(FAISS_PATH):
        shutil.rmtree(FAISS_PATH)

    from rag.retriever import invalidate_cache
    try:
        from rag.retriever import invalidate_cache
        invalidate_cache()
    except Exception:
        pass

    try:
        if pdf_file and pdf_file.filename:
            pdf_bytes = await pdf_file.read()

            from agents.pdf_agent import ingest_pdf_to_rag

            source_name = (
                f"pdf_{ticker}_{pdf_file.filename[:50]}"
            )

            success = ingest_pdf_to_rag(
                pdf_bytes,
                source_name,
            )

            if not success:
                print(
                    f"[API] PDF ingestion failed for "
                    f"{ticker}"
                )

        result = run_pipeline(
            query=query,
            ticker = ticker.upper().strip(),
        )

        if not result.get(
            "is_compliant",
            True,
        ):
            return {
                "status": "blocked",
                "ticker": ticker,
                "compliance_message":
                    result.get(
                        "compliance_message",
                        "",
                    ),
            }

        return {
            "status": "success",

            "ticker":
                result.get(
                    "company_ticker",
                    ticker,
                ),

            "report":
                result.get(
                    "final_report",
                    "",
                ),

            "report_id":
                result.get(
                    "report_id",
                ),

            "financial_metrics":
                result.get(
                    "financial_metrics",
                    {},
                ),

            "sentiment": {
                "label":
                    result.get(
                        "sentiment_label",
                        "Neutral",
                    ),
                "score":
                    result.get(
                        "sentiment_score",
                        0.0,
                    ),
            },

            "contagion_risks":
                result.get(
                    "contagion_risks",
                    [],
                ),

            "verified":
                result.get(
                    "verified",
                    False,
                ),

            "verification_notes":
                result.get(
                    "verification_notes",
                    "",
                ),

            "citations":
                result.get(
                    "citations",
                    [],
                ),

            "errors":
                result.get(
                    "errors",
                    [],
                ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:
        if os.path.exists(FAISS_PATH):
            shutil.rmtree(FAISS_PATH)

        try:
            from rag.retriever import invalidate_cache
            invalidate_cache()
        except Exception:
            pass

#Reports
@app.get("/reports")
def list_reports(
    db: Session = Depends(get_db),
    limit: int = 20,
    ticker: Optional[str] = None,
):
    #Get recent reports
    q = db.query(Report).order_by(Report.created_at.desc())
    if ticker:
        q = q.filter(Report.ticker == ticker.upper())
    reports = q.limit(limit).all()
    return [
        {
            "report_id": r.id,
            "ticker": r.ticker,
            "query": r.query[:80],
            "sentiment_label": r.sentiment_label,
            "sentiment_score": r.sentiment_score,
            "verified": r.verified,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]

@app.get("/reports/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    #Get full report by ID
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found.")
    return {
        "id": report.id,
        "ticker": report.ticker,
        "query": report.query,

        "final_report": report.final_report,

        "financial_metrics":
            report.financial_metrics,

        "contagion_risks":
            report.contagion_risks,

        "sentiment_label":
            report.sentiment_label,

        "sentiment_score":
            report.sentiment_score,

        "verified":
            report.verified,

        "citations":
            report.citations,

        "created_at":
            report.created_at.isoformat()
            if report.created_at
            else None,
    }

@app.delete("/reports/{report_id}")
def delete_report(report_id: str, db: Session = Depends(get_db)):
    #Delete report
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found.")
    db.delete(report)
    db.commit()
    return {"message": "Report deleted."}


#Watchlist
@app.post("/watchlist")
def add_to_watchlist(req: WatchlistRequest, db: Session = Depends(get_db)):
    existing = db.query(Watchlist).filter(
        Watchlist.ticker == req.ticker.upper()
    ).first()
    if existing:
        return {"message": f"{req.ticker.upper()} already in watchlist."}
    item = Watchlist(ticker=req.ticker.upper(), notes=req.notes or "")
    db.add(item)
    db.commit()
    return {"message": f"{req.ticker.upper()} added.", "id": item.id}

@app.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    items = db.query(Watchlist).order_by(Watchlist.added_at.desc()).all()
    return [
        {"id": i.id, "ticker": i.ticker, "notes": i.notes}
        for i in items
    ]

@app.delete("/watchlist/{ticker}")
def remove_from_watchlist(ticker: str, db: Session = Depends(get_db)):
    item = db.query(Watchlist).filter(
        Watchlist.ticker == ticker.upper()
    ).first()
    if not item:
        raise HTTPException(404, "Ticker not in watchlist.")
    db.delete(item)
    db.commit()
    return {"message": f"{ticker.upper()} removed."}


#Graph Stats
@app.get("/graph/stats")
def graph_stats():
    #Return GraphRAG graph statistics
    try:
        from graph.contagion import get_graph_stats
        return get_graph_stats()
    except Exception as e:
        return {"error": str(e)}

@app.get("/graph/risks/{ticker}")
def get_risks(ticker: str):
    #Get contagion risks for a ticker
    try:
        from graph.contagion import summarize_contagion
        risks = summarize_contagion(ticker)
        return {"ticker": ticker, "risks": risks, "count": len(risks)}
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV", "development") == "development",
    )