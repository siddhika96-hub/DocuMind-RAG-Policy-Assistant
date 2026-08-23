from app.database import SessionLocal
from app.retrieval.search import search, keyword_search, hybrid_search
from app.retrieval.embeddings import rerank

def test_dense_search():
    db = SessionLocal()
    results = search("What are the standard working hours?", db=db, top_k=3)
    db.close()
    print("Dense search:")
    for r in results:
        print(f"  Score: {r['score']:.4f} | {r['text'][:80]}...")


def test_keyword_search():
    db = SessionLocal()
    results = keyword_search("password security", db=db, top_k=3)
    db.close()
    print("\nKeyword search:")
    for r in results:
        print(f"  Score: {r['score']:.4f} | {r['text'][:80]}...")


def test_hybrid_search():
    db = SessionLocal()
    results = hybrid_search("Can I share my login with a coworker?", db=db, top_k=3)
    db.close()
    print("\nHybrid search:")
    for r in results:
        print(f"  Combined: {r['combined_score']:.4f} (Dense: {r['dense_score']:.4f}, Keyword: {r['keyword_score']:.4f})")


def test_reranking():
    db = SessionLocal()
    query = "What are the standard working hours?"
    candidates = hybrid_search(query, db=db, top_k=5)
    final = rerank(query, candidates, top_k=3)
    db.close()
    print("\nReranked results:")
    for r in final:
        print(f"  Rerank score: {r['rerank_score']:.4f} | {r['text'][:80]}...")


if __name__ == "__main__":
    test_dense_search()
    test_keyword_search()
    test_hybrid_search()
    test_reranking()