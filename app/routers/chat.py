import json
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.auth import verify_api_key
from app.retrieval.search import hybrid_search
from app.retrieval.embeddings import rerank
from app.generation.llm import generate_answer
from app.models import Message

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    top_k: int = 3
    session_id: str | None = None
    document_id: int | None = None


@router.post("/ask", dependencies=[Depends(verify_api_key)])
def ask_question(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())

    candidates = hybrid_search(
        request.question, db=db, top_k=request.top_k * 2, document_id=request.document_id
    )
    results = rerank(request.question, candidates, top_k=request.top_k)

    # Guard: if nothing was retrieved, don't call the LLM at all —
    # respond honestly instead of risking hallucination on empty context
    if not results:
        answer = "I don't have enough information to answer that. No relevant content was found in the selected document(s)."
        sources = []
    else:
        answer = generate_answer(request.question, results)
        sources = [r["metadata"] for r in results]

    message = Message(
        session_id=session_id,
        question=request.question,
        answer=answer,
        sources=json.dumps(sources),
    )
    db.add(message)
    db.commit()

    return {"session_id": session_id, "question": request.question, "answer": answer, "sources": sources}

@router.get("/history/{session_id}", dependencies=[Depends(verify_api_key)])
def get_history(session_id: str, db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at)
        .all()
    )
    return [
        {
            "question": m.question,
            "answer": m.answer,
            "sources": json.loads(m.sources),
            "created_at": m.created_at,
        }
        for m in messages
    ]