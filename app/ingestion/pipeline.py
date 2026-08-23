from sqlalchemy.orm import Session
from app.models import Document, Chunk
from app.ingestion.parser import extract_pages, extract_docx_pages, extract_txt_pages, extract_url_pages
from app.ingestion.chunker import split_text
from app.retrieval.embeddings import embed_texts


def ingest_document(pdf_path: str, filename: str, db: Session) -> Document:
    document = Document(filename=filename, status="processing")
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        ext = filename.lower().split(".")[-1]
        if ext == "pdf":
            pages = extract_pages(pdf_path)
        elif ext == "docx":
            pages = extract_docx_pages(pdf_path)
        elif ext == "txt":
            pages = extract_txt_pages(pdf_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        #  Chunk 
        all_chunks_text = []
        chunk_page_numbers = []
        for page in pages:
            page_chunks = split_text(page["text"])
            all_chunks_text.extend(page_chunks)
            chunk_page_numbers.extend([page["page_number"]] * len(page_chunks))

        #  Embed 
        embeddings = embed_texts(all_chunks_text)

        for text, page_number, embedding in zip(all_chunks_text, chunk_page_numbers, embeddings):
            chunk = Chunk(
                document_id=document.id,
                text=text,
                page_number=page_number,
                embedding=embedding,
            )
            db.add(chunk)

        document.status = "ready"
        db.commit()

    except Exception as e:
        document.status = "failed"
        db.commit()
        raise e

    return document


def ingest_url(url: str, db: Session) -> Document:
    document = Document(filename=url, status="processing")
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        pages = extract_url_pages(url)

        all_chunks_text = []
        chunk_page_numbers = []
        for page in pages:
            page_chunks = split_text(page["text"])
            all_chunks_text.extend(page_chunks)
            chunk_page_numbers.extend([page["page_number"]] * len(page_chunks))

        embeddings = embed_texts(all_chunks_text)

        for text, page_number, embedding in zip(all_chunks_text, chunk_page_numbers, embeddings):
            chunk = Chunk(
                document_id=document.id,
                text=text,
                page_number=page_number,
                embedding=embedding,
            )
            db.add(chunk)

        document.status = "ready"
        db.commit()

    except Exception as e:
        document.status = "failed"
        db.commit()
        raise e

    return document