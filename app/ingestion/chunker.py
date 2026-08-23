def split_text(text: str, chunk_size: int = 300, chunk_overlap: int = 50) -> list[str]:
    separators = ["\n\n", "\n", ". ", " ", ""]

    def _split(text: str, seps: list[str]) -> list[str]:
        if len(text) <= chunk_size:
            return [text]
        sep = seps[0]
        remaining_seps = seps[1:]
        if sep == "":
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        pieces = text.split(sep)
        chunks = []
        for piece in pieces:
            if len(piece) <= chunk_size:
                chunks.append(piece)
            else:
                chunks.extend(_split(piece, remaining_seps))
        return chunks

    raw_pieces = _split(text, separators)

    final_chunks = []
    current = ""
    for piece in raw_pieces:
        candidate = (current + " " + piece).strip() if current else piece
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                final_chunks.append(current)
                overlap_text = current[-chunk_overlap:] if len(current) > chunk_overlap else current
                current = (overlap_text + " " + piece).strip()
            else:
                final_chunks.append(piece)
                current = ""
    if current:
        final_chunks.append(current)
    return final_chunks