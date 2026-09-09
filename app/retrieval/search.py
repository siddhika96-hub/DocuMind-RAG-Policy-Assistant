from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import Chunk
from app.retrieval.embeddings import embed_query


def search(query: str, db: Session, top_k: int = 3, document_id: int | None = None) -> list[dict]:
    query_vector = embed_query(query)

    sql = """
        SELECT c.id, c.text, c.page_number, c.document_id, d.filename,
               1 - (c.embedding <=> :query_vector) AS similarity
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE 1=1
    """
    params = {"query_vector": str(query_vector), "top_k": top_k}

    if document_id is not None:
        sql += " AND c.document_id = :document_id"
        params["document_id"] = document_id

    sql += " ORDER BY c.embedding <=> :query_vector LIMIT :top_k"

    results = db.execute(text(sql), params).fetchall()

    return [
        {
            "id": row.id,
            "text": row.text,
            "score": row.similarity,
            "metadata": {"source": row.filename, "page": row.page_number},
        }
        for row in results
    ]

def keyword_search(query: str, db: Session, top_k: int = 5, document_id: int | None = None) -> list[dict]:
    sql = """
        SELECT c.id, c.text, c.page_number, c.document_id, d.filename,
               ts_rank(to_tsvector('english', c.text), plainto_tsquery('english', :query)) AS score
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE to_tsvector('english', c.text) @@ plainto_tsquery('english', :query)
    """
    params = {"query": query, "top_k": top_k}

    if document_id is not None:
        sql += " AND c.document_id = :document_id"
        params["document_id"] = document_id

    sql += " ORDER BY score DESC LIMIT :top_k"

    results = db.execute(text(sql), params).fetchall()

    return [
        {
            "id": row.id,
            "text": row.text,
            "score": row.score,
            "metadata": {"source": row.filename, "page": row.page_number},
        }
        for row in results
    ]

def hybrid_search(query: str, db: Session, top_k: int = 5, document_id: int | None = None) -> list[dict]:
    dense_results = search(query, db=db, top_k=top_k, document_id=document_id)
    keyword_results = keyword_search(query, db=db, top_k=top_k, document_id=document_id)

    combined = {}
    for r in dense_results:
        combined[r["id"]] = {
            "text": r["text"], "metadata": r["metadata"],
            "dense_score": r["score"], "keyword_score": 0.0,
        }
    for r in keyword_results:
        if r["id"] in combined:
            combined[r["id"]]["keyword_score"] = r["score"]
        else:
            combined[r["id"]] = {
                "text": r["text"], "metadata": r["metadata"],
                "dense_score": 0.0, "keyword_score": r["score"],
            }
    for item in combined.values():
        item["combined_score"] = (0.7 * item["dense_score"]) + (0.3 * item["keyword_score"])

    ranked = sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)
    return ranked[:top_k]