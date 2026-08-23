def build_prompt(query: str, results: list[dict]) -> str:
    context_blocks = []
    for i, r in enumerate(results):
        source = r["metadata"]["source"]
        page = r["metadata"]["page"]
        context_blocks.append(f"[Source {i+1}: {source}, page {page}]\n{r['text']}")

    context = "\n\n".join(context_blocks)

    return f"""You are a helpful HR policy assistant. Answer the question using ONLY the context provided below.

Rules:
- If the answer is not contained in the context, say "I don't have enough information to answer that."
- Do not use any outside knowledge.
- Cite the source number(s) you used, like [Source 1].

Context:
{context}

Question: {query}

Answer:"""