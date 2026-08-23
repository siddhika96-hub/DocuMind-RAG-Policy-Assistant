from app.database import SessionLocal
from app.retrieval.search import hybrid_search
from app.retrieval.embeddings import rerank

test_cases = [
    {"question": "Who owns the company policy manual?", "expected_keyword": "human resources department"},
    {"question": "Are employees allowed to share their passwords?", "expected_keyword": "passwords must never be shared"},
    {"question": "Can employees use AI tools for business activities?", "expected_keyword": "may use approved ai tools"},
    {"question": "Can records under legal hold be intentionally deleted?", "expected_keyword": "must not intentionally delete"},
    {"question": "What should happen to company property when employment ends?", "expected_keyword": "must be returned"},
    {"question": "Who should have access to customer personal information?", "expected_keyword": "authorized personnel"},
]

def evaluate(top_k: int = 3):
    db = SessionLocal()
    hits = 0

    for case in test_cases:
        candidates = hybrid_search(case["question"], db=db, top_k=top_k * 2)
        results = rerank(case["question"], candidates, top_k=top_k)

        retrieved_text = " ".join(r["text"] for r in results).lower()
        found = case["expected_keyword"].lower() in retrieved_text

        status = "✅ HIT" if found else "❌ MISS"
        print(f"{status} | {case['question']}")
        if not found:
            print(f"   Expected to find: '{case['expected_keyword']}'")
            print(f"   Actually retrieved:\n   {retrieved_text[:400]}")
            print()

        if found:
            hits += 1

    db.close()

    recall_at_k = hits / len(test_cases)
    print(f"\nRecall@{top_k}: {hits}/{len(test_cases)} = {recall_at_k:.1%}")


if __name__ == "__main__":
    evaluate(top_k=3)