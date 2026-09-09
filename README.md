# DocuMind — Intelligent Policy & Knowledge Assistant

A Retrieval-Augmented Generation (RAG) system that lets users upload documents (PDF, DOCX, TXT) or ingest web pages, then ask natural-language questions and receive accurate, cited answers grounded strictly in the source content — with no hallucinated information.

## Features

- **Multi-format ingestion** — PDF, DOCX, TXT, and live web page URLs
- **Background ingestion** — document uploads respond immediately; parsing, chunking, and embedding run asynchronously via FastAPI `BackgroundTasks`, so large uploads don't block the API
- **Hybrid retrieval** — combines dense semantic search (embeddings + cosine similarity via pgvector) with keyword-based full-text search (PostgreSQL), merged via weighted score fusion
- **Cross-encoder reranking** — refines hybrid search candidates using a query-passage cross-encoder for sharper relevance ranking
- **Per-document scoping** — retrieval can be scoped to a single document, preventing accuracy loss from unrelated documents competing in the same search
- **Grounded generation with an empty-context guard** — explicit hallucination-prevention prompting; verified to correctly decline out-of-scope questions. The LLM is never called when retrieval returns zero results, preventing a hallucination edge case found during testing
- **Prompt injection mitigation** — a hardened system prompt establishes retrieved content as data, not instructions, and an ingestion-time keyword scanner flags documents containing common injection patterns. Tested against a live, deliberately crafted injection attempt
- **API key authentication** — all endpoints require a valid `X-API-Key` header
- **Source citations** — every answer traces back to the originating document and page (where applicable)
- **Persistent conversation history** — session-based multi-turn chat, stored and retrievable
- **Document management** — upload, list, and delete documents via REST API, with cascading cleanup of associated chunks
- **Streamlit chat interface** — full working frontend, not just an API

## Architecture

**Ingestion pipeline:**
```
Document (PDF/DOCX/TXT) or URL
    → Upload endpoint creates Document record (status: processing), responds immediately
    → [Background task] Parse & clean text → scan for injection patterns
    → Chunk (recursive splitting with overlap)
    → Embed (Sentence-Transformers)
    → Store in PostgreSQL + pgvector → status: ready
```

**Query pipeline:**
```
User question (+ API key, optional document_id)
    → Verify API key
    → Embed query
    → Dense search (pgvector) + Keyword search (PostgreSQL full-text), optionally scoped to one document
    → Merge via weighted fusion (hybrid search)
    → Cross-encoder reranking
    → If zero results: return "no information found" — LLM is never called
    → Otherwise: construct grounded, injection-resistant prompt with citations
    → LLM generation (Hugging Face Inference API)
    → Answer + sources, persisted to conversation history
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI, SQLAlchemy |
| Database | PostgreSQL + pgvector (hosted on Supabase) |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`, 384-dim) |
| Reranking | Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) |
| LLM | Hugging Face Inference API |
| Frontend | Streamlit |
| Document parsing | pypdf, python-docx, BeautifulSoup |
| Auth | API key via custom FastAPI dependency |

## Project Structure

```
policy-assistant/
├── app/
│   ├── main.py               # FastAPI app entrypoint
│   ├── database.py            # DB connection / session management
│   ├── models.py               # SQLAlchemy models (Document, Chunk, Message)
│   ├── auth.py                  # API key verification dependency
│   ├── ingestion/
│   │   ├── parser.py            # PDF/DOCX/TXT/URL text extraction, cleaning, injection scanning
│   │   ├── chunker.py            # Recursive text splitting with overlap
│   │   └── pipeline.py            # Ingestion orchestration, incl. background processing
│   ├── retrieval/
│   │   ├── embeddings.py          # Embedding model + cross-encoder reranker
│   │   └── search.py               # Dense, keyword, and hybrid search (with document scoping)
│   ├── generation/
│   │   ├── prompts.py               # Grounded, injection-resistant prompt construction
│   │   └── llm.py                    # LLM API calls
│   └── routers/
│       ├── documents.py               # Upload/list/delete endpoints (API key protected)
│       └── chat.py                     # Ask/history endpoints (API key protected)
├── tests/                     # Manual verification scripts per pipeline stage
├── evaluate.py                 # Retrieval evaluation (Recall@K)
├── check_models.py              # Utility: lists live HF models for your token
├── create_tables.py              # One-time DB table creation
├── frontend.py                    # Streamlit chat UI
├── requirements.txt
└── .env                            # Secrets (gitignored): DATABASE_URL, HF_TOKEN, API_SECRET_KEY
```

## Evaluation

Retrieval quality is measured using Recall@K on a hand-built test set of representative questions with known-correct answers verified against source documents.

Run: `python evaluate.py`

**Note on scope:** the test set is intentionally small and self-authored. It's sufficient to validate that the retrieval pipeline works correctly end-to-end, but is not a substitute for a larger, independently-labeled evaluation set. During development, this process also surfaced a real methodology bug — an early version of the eval checked for paraphrased "ideal answers" rather than actual source-document phrases, producing a misleading recall score. Fixing the evaluation itself (not the retrieval system) resolved it.

## Security

- **Authentication:** all endpoints require an `X-API-Key` header matching a server-side secret. Requests without a valid key receive `401 Unauthorized`.
- **SQL injection:** all database queries use parameterized SQL (SQLAlchemy `text()` with named bind parameters), never string concatenation of user input.
- **Prompt injection:** mitigated via (1) a system prompt that explicitly treats retrieved content as data, never as instructions, and (2) a keyword-based scanner that flags documents containing common injection phrases during ingestion. Tested with a deliberately crafted injection document — the system correctly ignored embedded instructions and answered only from legitimate content. This is a mitigation, not a complete solution; prompt injection remains an open problem in the field, and a more robust system would use a dedicated classifier rather than keyword matching.
- **Secrets management:** all credentials (`DATABASE_URL`, `HF_TOKEN`, `API_SECRET_KEY`) are loaded from environment variables, never hardcoded, never committed to version control.

## Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd policy-assistant

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1      # Windows
source venv/bin/activate        # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Create a .env file with:
#   DATABASE_URL=postgresql://...  (Supabase or any pgvector-enabled Postgres)
#   HF_TOKEN=hf_...                (free at huggingface.co/settings/tokens)
#   API_SECRET_KEY=...             (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")

# 5. Create database tables
python create_tables.py

# 6. Run the backend
uvicorn app.main:app --reload

# 7. In a separate terminal, run the frontend
streamlit run frontend.py
```

Visit `http://localhost:8501` for the chat interface, or `http://127.0.0.1:8000/docs` for the interactive API documentation (use the "Authorize" button to enter your API key).

## Known Limitations & Future Work

Being upfront about these — they're deliberate scope decisions for an MVP, not oversights:

- **Chunking is length-based, not structure-aware.** It can occasionally merge the end of one document section with the start of an unrelated one, diluting that chunk's embedding. Reranking mitigates but doesn't fully solve this.
- **No table extraction.** Tables inside PDFs are extracted as plain text, which can lose structure.
- **No OCR support.** Scanned/image-based PDFs are not supported — only PDFs with a real text layer.
- **LLM provider dependency is a real fragility.** Hugging Face's free-tier model routing changes over time — a model that works today may stop being available later (encountered directly during development, twice). A production system would use a paid, SLA-backed provider or self-hosted model.
- **Authentication is a single shared API key, not per-user accounts.** Sufficient to prevent anonymous public access, but not suitable for multi-tenant use with per-user permissions.
- **Prompt injection defenses are mitigations, not guarantees.** The keyword-based scanner can be bypassed by rephrasing; the hardened system prompt is the more robust layer but is not a formal guarantee against all injection techniques.
- **Hybrid search fusion weights (0.7 dense / 0.3 keyword) are hand-picked defaults**, not tuned or learned from data.
- **Evaluation set is small.** Sufficient to validate correctness, insufficient to make strong quantitative claims about retrieval quality at scale.

## What I'd Improve With More Time

- Structure-aware chunking using document headings as hard chunk boundaries
- A dedicated classifier for prompt injection detection, rather than keyword matching
- Per-user authentication and multi-tenant document isolation
- Larger, more rigorous evaluation set with generation-quality metrics (faithfulness, answer relevance)
- Table-aware PDF extraction (`pdfplumber`) for structured data like leave-day tables
- Dockerization and containerized deployment
- Automated CI test suite