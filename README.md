# DocuMind — RAG Policy & Knowledge Assistant

An intelligent **Retrieval-Augmented Generation (RAG)** system that allows users to upload documents or ingest web pages, ask natural-language questions, and receive **grounded answers with source citations**.

The system is designed to minimize hallucinations by generating answers strictly from retrieved source content and declining questions that cannot be answered from the available knowledge base.

---

## ✨ Features

* **Multi-format ingestion** — PDF, DOCX, TXT, and web pages
* **Hybrid retrieval** — combines semantic vector search with PostgreSQL full-text search
* **Cross-encoder reranking** — improves relevance of retrieved passages
* **Grounded generation** — prompts the LLM to answer only from retrieved context
* **Source citations** — answers include the originating document and page where applicable
* **Conversation history** — supports persistent session-based multi-turn conversations
* **Document management** — upload, list, and delete documents through REST APIs
* **Streamlit interface** — complete working chat frontend
* **Retrieval evaluation** — measures retrieval performance using Recall@K

---

## 🧠 RAG Architecture

### Ingestion Pipeline

```text
Document / Web URL
        ↓
Parse & Clean Text
        ↓
Recursive Chunking
        ↓
Generate Embeddings
        ↓
PostgreSQL + pgvector
```

Supported sources:

```text
PDF ──────┐
DOCX ─────┤
TXT ──────┼──→ Text Extraction → Chunking → Embeddings → Database
Web URL ──┘
```

### Query Pipeline

```text
User Question
      ↓
Query Embedding
      ↓
 ┌───────────────────────┐
 │                       │
 ▼                       ▼
Dense Search       Keyword Search
(pgvector)        (PostgreSQL FTS)
 │                       │
 └──────────┬────────────┘
            ↓
      Weighted Fusion
      (Hybrid Search)
            ↓
   Cross-Encoder Reranking
            ↓
   Grounded Prompt + Sources
            ↓
     Hugging Face LLM
            ↓
     Answer + Citations
            ↓
   Conversation History
```

### Retrieval Strategy

The system combines:

**1. Dense Semantic Search**

Uses Sentence-Transformers embeddings and pgvector cosine similarity to retrieve semantically similar chunks.

**2. Keyword Search**

Uses PostgreSQL full-text search to capture exact keyword and terminology matches.

**3. Hybrid Search**

Dense and keyword results are merged using weighted score fusion.

Default weighting:

```text
Dense retrieval   → 0.7
Keyword retrieval → 0.3
```

**4. Cross-Encoder Reranking**

The retrieved candidates are passed through a cross-encoder to produce a more accurate relevance ranking before generation.

---

## 🛠️ Tech Stack

| Component        | Technology                             |
| ---------------- | -------------------------------------- |
| Backend          | FastAPI                                |
| ORM              | SQLAlchemy                             |
| Database         | PostgreSQL + pgvector                  |
| Database Hosting | Supabase                               |
| Embeddings       | Sentence-Transformers                  |
| Embedding Model  | `all-MiniLM-L6-v2`                     |
| Reranker         | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| LLM              | Hugging Face Inference API             |
| Frontend         | Streamlit                              |
| PDF Parsing      | pypdf                                  |
| DOCX Parsing     | python-docx                            |
| Web Parsing      | BeautifulSoup                          |
| Evaluation       | Recall@K                               |

---

## 📁 Project Structure

```text
policy-assistant/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   │
│   ├── ingestion/
│   │   ├── parser.py
│   │   └── chunker.py
│   │
│   ├── retrieval/
│   │   ├── embeddings.py
│   │   └── search.py
│   │
│   ├── generation/
│   │   ├── prompts.py
│   │   └── llm.py
│   │
│   └── routers/
│       ├── documents.py
│       └── chat.py
│
├── tests/
│   └── Pipeline verification scripts
│
├── create_tables.py
├── evaluate.py
├── frontend.py
├── HF_models.py
├── requirements.txt
├── README.md
└── .gitignore
```

### Key Components

| File            | Purpose                                     |
| --------------- | ------------------------------------------- |
| `main.py`       | FastAPI application entry point             |
| `parser.py`     | PDF, DOCX, TXT, and URL text extraction     |
| `chunker.py`    | Recursive text splitting with overlap       |
| `embeddings.py` | Embedding generation and reranking          |
| `search.py`     | Dense, keyword, and hybrid retrieval        |
| `prompts.py`    | Grounded prompt construction                |
| `llm.py`        | Hugging Face LLM integration                |
| `documents.py`  | Document management APIs                    |
| `chat.py`       | Question answering and conversation history |
| `frontend.py`   | Streamlit chat interface                    |
| `evaluate.py`   | Retrieval evaluation using Recall@K         |

---

## 📊 Evaluation

Retrieval quality is evaluated using **Recall@K** on a manually created test set containing representative questions with known relevant source content.

Run the evaluation with:

```bash
python evaluate.py
```

### Evaluation Methodology

The evaluation dataset is intentionally small and self-authored. It is designed to validate that the retrieval pipeline works correctly end-to-end rather than make broad quantitative claims about production-scale performance.

During development, an evaluation methodology issue was discovered where the initial implementation compared retrieved content against **paraphrased ideal answers instead of actual source-document content**.

This produced misleading retrieval results.

The evaluation was corrected to verify retrieved chunks against the actual source content, and reported failures were manually inspected rather than relying solely on aggregate Recall@K scores.

This helped validate the evaluation methodology itself before using it to judge retrieval quality.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/siddhika96-hub/DocuMind-RAG-Policy-Assistant.git
cd DocuMind-RAG-Policy-Assistant
```

### 2. Create a Virtual Environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://...
HF_TOKEN=hf_...
```

> Never commit your `.env` file. It contains private credentials.

### 5. Create Database Tables

```bash
python create_tables.py
```

### 6. Start the FastAPI Backend

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 7. Start the Streamlit Frontend

Open another terminal:

```bash
streamlit run frontend.py
```

Open:

```text
http://localhost:8501
```

---

## 💬 Example Workflow

```text
1. Upload a company policy PDF
             ↓
2. Document is parsed and chunked
             ↓
3. Chunks are embedded and stored
             ↓
4. Ask a question
             ↓
5. Hybrid retrieval finds relevant chunks
             ↓
6. Cross-encoder reranks the results
             ↓
7. LLM receives only retrieved context
             ↓
8. Grounded answer + source citation
```

Example:

**Question**

> Can employees use AI tools for business activities?

**Response**

The assistant generates an answer based on the uploaded policy and provides the relevant source citation.

If the knowledge base does not contain enough information to answer a question, the system is instructed to **decline instead of fabricating an answer**.

---

## ⚠️ Known Limitations

### Per-document retrieval

Queries currently search across all ingested documents. When multiple unrelated documents are present, irrelevant chunks can compete with relevant ones.

**Future improvement:** metadata-based document filtering and per-document retrieval.

### Structure-aware chunking

Chunking is currently length-based. It does not explicitly understand document headings or section boundaries.

**Future improvement:** heading-aware and structure-aware chunking.

### PDF Tables

Tables are currently extracted as plain text, which can result in loss of their original structure.

**Future improvement:** table-aware extraction using tools such as `pdfplumber`.

### OCR

Scanned or image-based PDFs are not currently supported because they do not contain a machine-readable text layer.

**Future improvement:** OCR integration.

### LLM Provider Dependency

The project uses the Hugging Face Inference API. Free-tier model availability and routing can change over time.

**Future improvement:** support for configurable LLM providers or self-hosted models.

### Authentication

Authentication and authorization are not currently implemented.

**Future improvement:** user authentication, document ownership, and multi-tenant isolation.

### Retrieval Weights

The hybrid retrieval weights (`0.7` dense / `0.3` keyword) are manually selected and have not been optimized against a large labeled dataset.

### Evaluation Dataset

The current evaluation set is small and self-authored.

It is useful for validating the retrieval pipeline but is not sufficient for making strong claims about large-scale retrieval performance.

---

## 🔮 Future Improvements

* [ ] Per-document and metadata-scoped retrieval
* [ ] Structure-aware chunking
* [ ] Larger and independently labeled evaluation dataset
* [ ] Generation evaluation using faithfulness and answer relevance metrics
* [ ] Table-aware PDF extraction
* [ ] OCR support for scanned documents
* [ ] Authentication and multi-tenant document isolation
* [ ] Automated CI test suite
* [ ] Dockerization
* [ ] Cloud deployment

---

## 🎯 Project Highlights

This project demonstrates practical implementation of a production-oriented RAG pipeline, including:

* Document ingestion and preprocessing
* Recursive text chunking
* Vector embeddings
* PostgreSQL + pgvector
* Hybrid retrieval
* Cross-encoder reranking
* Grounded LLM generation
* Source attribution
* Conversation memory
* REST API development with FastAPI
* RAG evaluation using Recall@K
* Debugging and validation of evaluation methodology


