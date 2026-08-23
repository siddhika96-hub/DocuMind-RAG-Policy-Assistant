Intelligent Policy & Knowledge Assistant

A Retrieval-Augmented Generation (RAG) system that lets users upload documents (PDF, DOCX, TXT) or ingest web pages, then ask natural-language questions and receive accurate, cited answers grounded strictly in the source content — with no hallucinated information.

Features
-Multi-format ingestion — PDF, DOCX, TXT, and live web page URLs
-Hybrid retrieval — combines dense semantic search (embeddings + cosine similarity via pgvector) with keyword-based full-text search (PostgreSQL), merged via weighted score fusion
-Cross-encoder reranking — refines hybrid search candidates using a query-passage cross-encoder for sharper relevance ranking
-Grounded generation — explicit hallucination-prevention prompting; verified to correctly decline out-of-scope questions instead of fabricating answers
-Source citations — every answer traces back to the originating document and page (where applicable)
-Persistent conversation history — session-based multi-turn chat, stored and retrievable
-Document management — upload, list, and delete documents via REST API, with cascading cleanup of associated chunks
-Streamlit chat interface — full working frontend, not just an API

*Architecture

Ingestion pipeline:

Document (PDF/DOCX/TXT) or URL
    → Parse & clean text
    → Chunk (recursive splitting with overlap)
    → Embed (Sentence-Transformers)
    → Store in PostgreSQL + pgvector

Query pipeline:

User question
    → Embed query
    → Dense search (pgvector cosine similarity) + Keyword search (PostgreSQL full-text)
    → Merge via weighted fusion (hybrid search)
    → Cross-encoder reranking
    → Construct grounded prompt with citations
    → LLM generation (Hugging Face Inference API)
    → Answer + sources, persisted to conversation history

**Tech Stack

Layer	Technology
Backend API	FastAPI, SQLAlchemy
Database	PostgreSQL + pgvector (hosted on Supabase)
Embeddings	Sentence-Transformers (all-MiniLM-L6-v2, 384-dim)
Reranking	Cross-Encoder (cross-encoder/ms-marco-MiniLM-L-6-v2)
LLM	Hugging Face Inference API
Frontend	Streamlit
Document parsing	pypdf, python-docx, BeautifulSoup

Project Structure

policy-assistant/
├── app/
│   ├── main.py               # FastAPI app entrypoint
│   ├── database.py            # DB connection / session management
│   ├── models.py               # SQLAlchemy models (Document, Chunk, Message)
│   ├── ingestion/
│   │   ├── parser.py            # PDF/DOCX/TXT/URL text extraction + cleaning
│   │   └── chunker.py            # Recursive text splitting with overlap
│   ├── retrieval/
│   │   ├── embeddings.py          # Embedding model + cross-encoder reranker
│   │   └── search.py               # Dense, keyword, and hybrid search
│   ├── generation/
│   │   ├── prompts.py               # Grounded prompt construction
│   │   └── llm.py                    # LLM API calls
│   └── routers/
│       ├── documents.py               # Upload/list/delete endpoints
│       └── chat.py                     # Ask/history endpoints
├── tests/                     # Manual verification scripts per pipeline stage
├── evaluate.py                 # Retrieval evaluation (Recall@K)
├── check_models.py              # Utility: lists live HF models for your token
├── create_tables.py              # One-time DB table creation
├── frontend.py                    # Streamlit chat UI
├── requirements.txt
└── .env                            # Secrets (gitignored)
Evaluation

Retrieval quality is measured using Recall@K on a hand-built test set of representative questions with known-correct answers verified against source documents.

Run: python evaluate.py

Note on scope: the test set is intentionally small and self-authored. It's sufficient to validate that the retrieval pipeline works correctly end-to-end, but is not a substitute for a larger, independently-labeled evaluation set. During development, this process also surfaced a real methodology bug — an early version of the eval checked for paraphrased "ideal answers" rather than actual source-document phrases, producing a misleading recall score. Fixing the evaluation itself (not the retrieval system) resolved it. This was confirmed by inspecting the actual retrieved chunks on each reported failure, rather than trusting the aggregate score alone.

Setup
bash
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

# 5. Create database tables
python create_tables.py

# 6. Run the backend
uvicorn app.main:app --reload

# 7. In a separate terminal, run the frontend
streamlit run frontend.py

Visit http://localhost:8501 for the chat interface, or http://127.0.0.1:8000/docs for the interactive API documentation.

***Known Limitations & Future Work

Being upfront about these — they're deliberate scope decisions for an MVP, not oversights:

Retrieval searches across all ingested documents with no per-document scoping. Discovered during testing: querying with multiple unrelated documents in the database can dilute retrieval quality, since relevant and irrelevant chunks are ranked together indiscriminately.
 A production version would let users scope a query to one document or a document set via metadata filtering.

Chunking is length-based, not structure-aware. It can occasionally merge the end of one document section with the start of an unrelated one, diluting that chunk's embedding. Reranking mitigates but doesn't fully solve this.

No table extraction.- Tables inside PDFs are extracted as plain text, which can lose structure.

No OCR support- Scanned/image-based PDFs are not supported — only PDFs with a real text layer.

LLM provider dependency is a real fragility. Hugging Face's free-tier model routing changes over time — a model that works today may stop being available later (encountered directly during development, twice). A production system would use a paid, SLA-backed provider or self-hosted model.

No authentication- Any client can upload documents or query the system. Not suitable for multi-tenant use as-is.

Hybrid search fusion weights (0.7 dense / 0.3 keyword) are hand-picked defaults, not tuned or learned from data.

Evaluation set is small-Sufficient to validate correctness, insufficient to make strong quantitative claims about retrieval quality at scale.


What I'd Improve With More Time....
-Per-document / metadata-scoped retrieval
-Structure-aware chunking using document headings as hard chunk boundaries
-Larger, more rigorous evaluation set with generation-quality metrics (faithfulness, answer relevance), not just retrieval Recall@K
-Table-aware PDF extraction (pdfplumber) for structured data like leave-day tables
-Authentication and multi-tenant document isolation
-Dockerization and cloud deployment
-Automated CI test suite