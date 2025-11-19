# RFP Analyzer (Backend)

This is the FastAPI + Celery service that ingests PDFs, chunks them, summarizes the relevant passages, and extracts 15 procurement traits with evidence. Follow the steps below exactly—no guesswork required.

---

## 1. What you need first

### Linux / Ubuntu
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git redis-server postgresql \
    tesseract-ocr poppler-utils libmagic-dev libgl1
```
Make sure PostgreSQL and Redis are running (`sudo systemctl status postgresql redis-server`).

### Windows 11 / 10
Open **PowerShell as Administrator**:
```powershell
wsl --install      # optional but recommended for Linux tooling
winget install Python.Python.3.11
winget install Git.Git
winget install Redis.Redis-Server
winget install PostgreSQL.PostgreSQL
winget install UB-Mannheim.TesseractOCR
winget install Poppler
```
Restart PowerShell after installs finish. If you prefer WSL, run the Linux commands inside Ubuntu instead.

---

## 2. Clone the repo
```bash
git clone https://github.com/harish-bodduna/rfp_analyzer.git
cd rfp_analyzer
```

---

## 3. Create and activate a Python environment

### Linux / Ubuntu
```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### Windows (PowerShell)
```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
```

Keep this terminal open; you’ll run all backend commands here.

---

## 4. Install Python dependencies
```bash
pip install -e .
```
If PyTorch or transformers need CUDA, install the matching wheels for your GPU stack.

---

## 5. Configure environment variables
Copy the example file and edit it:

### Linux / Ubuntu
```bash
cp .env.example .env
nano .env      # or your favorite editor
```

### Windows (PowerShell)
```powershell
copy .env.example .env
notepad .env
```

Set at least these keys:
```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/rfp_analyzer
REDIS_URL=redis://localhost:6379/0
TRANSFORMER_LLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
TRANSFORMER_LLM_MODELS=["meta-llama/Meta-Llama-3.1-8B-Instruct","google/flan-t5-large"]
TRANSFORMER_EMBED_MODEL=intfloat/e5-large-v2
TRANSFORMER_DEVICE=cuda:0        # use cpu if no GPU
DATA_ROOT=data
RAW_FILES_DIR=data/raw_files
PROCESSED_FILES_DIR=data/processed_files
UPLOADED_FILES_DIR=data/uploaded_files
```
Add API keys or model paths as needed.

---

## 6. Prep the database
1. Create a database in Postgres: `createdb rfp_analyzer` (Linux) or use pgAdmin/DBeaver on Windows.
2. Run migrations or let the ORM create tables on first use (current MVP auto-creates via SQLModel).

---

## 7. Start backend services

### Terminal 1 – FastAPI API
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2 – Celery worker
Activate the same virtualenv, then:
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

Both terminals must stay open while processing PDFs.

---

## 8. Test that everything works
1. `curl http://localhost:8000/health` should return `{"status":"ok"}`.
2. Use the frontend (see `rfp_insights_dashboard` repo) or Swagger at `http://localhost:8000/docs` to upload a PDF.
3. Watch the Celery logs for status changes (`UPLOADED -> IN_FLIGHT -> PROCESSING -> COMPLETED`).

---

## 9. Useful directories
- `app/` – FastAPI routes, services, Celery tasks.
- `data/raw_files` – PDFs as uploaded.
- `data/processed_files` – chunk metadata snapshots.
- `data/uploaded_files` – UI uploads awaiting processing.

---

## 10. Need help?
- If the model downloads are slow or gated, log in to Hugging Face first: `huggingface-cli login`.
- For GPU issues, ensure the NVIDIA drivers & CUDA toolkit match your torch build.
- For networking (accessing from another laptop), bind FastAPI to `0.0.0.0` and use your LAN IP.

That’s it—follow the steps in order and the backend will be up even if you’re brand new to Python services.
