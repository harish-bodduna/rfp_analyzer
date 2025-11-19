# RFP Analyzer

Backend services for automating extraction of structured traits from RFP/RFQ documents. Upload PDFs, process them asynchronously, and return standardized traits with provenance.

## Key Features
- FastAPI-based API for uploads, processing, and retrieval of extracted traits
- Celery worker pipeline for parsing, chunking, summarization, embeddings, and trait extraction
- Support for OpenAI LLM/embedding APIs
- Storage strategy that keeps raw PDFs, structured metadata, sections, chunks, and summaries
- Configurable trait definitions (15 trait MVP)

## Getting Started
1. Create a Python 3.11+ virtual environment.
2. Install dependencies (plus system packages for PDF parsing):
   ```bash
   sudo apt install -y tesseract-ocr poppler-utils libmagic-dev libgl1
   pip install -e .
   ```
3. Copy `.env.example` to `.env` and customize settings (DB URLs, OpenAI keys, file paths).
4. Run the API server:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Start Celery workers:
   ```bash
   celery -A app.workers.celery_app worker -l info
   ```

### Environment Variables
At minimum configure the following keys in `.env`:

```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/rfp_analyzer
REDIS_URL=redis://localhost:6379/0
LLM_PROVIDER=transformers
EMBED_PROVIDER=transformers
OPENAI_API_KEY=
TRANSFORMER_LLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
TRANSFORMER_LLM_MODELS=["meta-llama/Meta-Llama-3.1-8B-Instruct","google/flan-t5-large"]
TRANSFORMER_EMBED_MODEL=intfloat/e5-large-v2
TRANSFORMER_DEVICE=cuda:0
TRANSFORMER_MAX_NEW_TOKENS=512
DATA_ROOT=data
RAW_FILES_DIR=data/raw_files
PROCESSED_FILES_DIR=data/processed_files
UPLOADED_FILES_DIR=data/uploaded_files
```

Flip both providers to `openai` and set `OPENAI_API_KEY` when you regain API access.

## Directory Layout
- `app/`: Application code organized by API, core config, database models, schemas, services, utils, and Celery workers
- `data/raw_files`, `data/processed_files`, `data/uploaded_files`: Storage locations for documents and derived assets
- `scripts/`: Utilities such as data seeding or evaluation helpers
- `tests/`: Automated tests (to be added)

## Status
This is an initial scaffolding to accelerate iteration on parsing, retrieval, and trait extraction. Additional implementation details, tests, and deployment scripts will be layered on top.
