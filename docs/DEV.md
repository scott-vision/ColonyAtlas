# Development

## Local (no Docker)

Backend:

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Note: for GPU acceleration with Cellpose, install a CUDA-enabled PyTorch build before
`pip install -r requirements.txt` (see the PyTorch install selector for your CUDA version).

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:
- Frontend: http://localhost:3000/upload
- Backend OpenAPI: http://localhost:8000/docs

## Docker Compose

```bash
docker compose up --build
```

Open:
- Frontend: http://localhost:3000/upload
- Backend OpenAPI: http://localhost:8000/docs
```
