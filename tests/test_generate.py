from app.database import SessionLocal
from app.retrieval.search import hybrid_search
from app.retrieval.embeddings import rerank
from app.generation.llm import generate_answer

db = SessionLocal()

query = "What are the standard working hours?"

candidates = hybrid_search(query, db=db, top_k=6)
results = rerank(query, candidates, top_k=3)
answer = generate_answer(query, results)

print(f"Question: {query}\n")
print(f"Answer: {answer}")

db.close()