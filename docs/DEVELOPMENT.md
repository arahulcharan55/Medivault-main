# Development

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=. python scripts/seed_demo.py
uvicorn app.main:app --reload --port 8000
```

## Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Generate sample PDF

```bash
cd backend && source .venv/bin/activate
pip install fpdf2
python - <<'PY'
from fpdf import FPDF
from pathlib import Path
text = Path('../samples/demo-lab-report.txt').read_text().splitlines()
pdf = FPDF(); pdf.add_page(); pdf.set_font('Helvetica', size=12)
for line in text: pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
pdf.output('../samples/demo-lab-report.pdf')
PY
```

## Run tests

```bash
cd backend && source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

## Environment

See [ENVIRONMENT.md](./ENVIRONMENT.md) and `backend/.env.example`.
