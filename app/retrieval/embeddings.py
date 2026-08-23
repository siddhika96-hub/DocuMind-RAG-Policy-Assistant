from sentence_transformers import SentenceTransformer,CrossEncoder

_model = SentenceTransformer("all-MiniLM-L6-v2")
_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeds a list of strings, returns a list of 384-dim vectors."""
    embeddings = _model.encode(texts)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Embeds a single query string, returns one 384-dim vector."""
    embedding = _model.encode([query])[0]
    return embedding.tolist()

def rerank(query: str, candidates: list[dict], top_k: int = 3) -> list[dict]:
    pairs = [[query, c["text"]] for c in candidates]
    scores = _reranker.predict(pairs)

    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]