# Competitive Programming Copilot

An algorithmic tutoring assistant that guides you toward solving problems yourself instead of dumping full code. It combines **RAG**, **AST analysis** of your code (Tree-sitter), and a **Code Lock** that blocks solution generation until you explicitly unlock it.

Paste a problem, describe your approach, or share broken code — the copilot returns hints grounded in similar problems and algorithmic concepts.

## Features

| Mode | Purpose |
|---|---|
| **Brainstorming** | Pick a technique (two pointers, DP, graphs, …) — no code |
| **Complexity** | Derive time/space complexity and TLE risk |
| **Rubber duck** | Find logic bugs in your code via guiding questions |
| **Code unlocked** | Full reference solutions (only after you click *Unlock code*) |

**Code Lock** works on two levels:

1. **System prompt** — while locked, the LLM must not output code blocks.
2. **RAG** — the `code_solutions` collection is queried only when unlocked, so reference implementations never enter context in hint mode.

User code is not embedded raw. Tree-sitter extracts structural signals (functions, loop nesting, recursion, estimated complexity) for both the vector query and the LLM context.

## Architecture

```
React (Vite) ──JSON──> FastAPI ──> Tree-sitter (user code AST)
                          │
                          ├──> Qdrant (hybrid RAG: dense + BM25)
                          │      ├─ conceptual_data  (concepts + editorials)
                          │      └─ code_solutions   (reference code — unlocked only)
                          │
                          └──> LLM (OpenAI-compatible API)
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- No Docker required (Qdrant runs embedded on disk)

Optional: an LLM API key (OpenAI, Gemini via OpenAI-compatible endpoint, or a local server like Ollama). Without it, the app runs in **demo mode** and still performs RAG + AST analysis.

## Quick start

### 1. First-time setup

```bash
# Backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # optional: add LLM key later
.venv/bin/python ingest.py      # load knowledge base into Qdrant

# Frontend
cd ../frontend
npm install
```

### 2. Run both services

From the project root:

```bash
./start.sh
```

- **Frontend:** http://localhost:5173  
- **Backend API:** http://localhost:8000  
- **API docs:** http://localhost:8000/docs  

Press `Ctrl+C` to stop both processes.

### Manual start (alternative)

```bash
# Terminal 1 — backend
cd backend
.venv/bin/uvicorn app.main:app --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

## LLM configuration

Copy `backend/.env.example` to `backend/.env` and configure one of the options below. Restart the backend after changes.

### OpenAI

```env
OPENAI_API_KEY=sk-your-real-key
LLM_MODEL=gpt-4o-mini
```

### Gemini (OpenAI-compatible endpoint)

```env
OPENAI_API_KEY=your-gemini-api-key
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-2.0-flash
```

Get a key at [Google AI Studio](https://aistudio.google.com/apikey).

### Local model (Ollama, LM Studio, vLLM)

```env
OPENAI_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5-coder:14b
OPENAI_API_KEY=not-needed
```

### Demo mode (no LLM)

Leave `OPENAI_API_KEY` empty. The chat still returns RAG matches and AST metadata, with a note that full LLM responses require configuration.

> Do not leave the placeholder `sk-...` from older templates — it will be treated as invalid.

## Extending the knowledge base

The RAG corpus lives in JSON files under `backend/data/`. After any edit, re-run ingest (this recreates Qdrant collections):

```bash
cd backend
.venv/bin/python ingest.py
```

### `backend/data/concepts/concepts.json`

Algorithmic concepts, patterns, and complexity notes. Each entry:

```json
{
  "title": "Two Pointers",
  "kind": "concept",
  "text": "Long-form explanation used for embedding and retrieval..."
}
```

Use this for techniques (sliding window, DP, graphs, common pitfalls, TLE rules, etc.).

### `backend/data/solutions/problems.json`

Solved problems with editorials and reference code (Python). Each entry:

```json
{
  "title": "Two Sum",
  "source": "LeetCode 1",
  "difficulty": "easy",
  "tags": ["hash map", "array"],
  "editorial": "Approach explanation, complexity, common mistakes...",
  "code": "def two_sum(nums, target):\n    ...",
  "code_language": "python"
}
```

- **Editorials** are indexed in `conceptual_data` (available in all modes).
- **Reference code** is indexed in `code_solutions` (retrieved only when Code Lock is off).

Add as many entries as you need, then run `ingest.py` again.

## API

`POST /api/chat`

```json
{
  "user_query": "Which approach fits this problem?",
  "user_code": "",
  "task_context": "Given an array, find two numbers that sum to target...",
  "current_mode": "brainstorming",
  "code_unlocked": false,
  "history": []
}
```

`current_mode`: `brainstorming` | `complexity` | `hint`

Response includes `response`, `retrieved` (RAG hits), and `code_analysis` (AST, when code is provided).

## Project structure

```
backend/
  app/
    main.py           # FastAPI — chat endpoint
    prompts.py        # dynamic system prompt + Code Lock
    rag.py            # Qdrant hybrid search
    ast_analyzer.py   # Tree-sitter code analysis
    llm.py            # OpenAI-compatible client + demo fallback
    models.py         # request/response schemas
    config.py         # settings from .env
  data/
    concepts/concepts.json    # extend knowledge base (concepts)
    solutions/problems.json   # extend knowledge base (problems + code)
  ingest.py           # load JSON → Qdrant
  qdrant_storage/     # embedded vector DB (created by ingest)
  .env.example
frontend/
  src/
    App.jsx
    components/NavBar.jsx
    components/AnalysisPanel.jsx
start.sh              # run backend + frontend
```

## Troubleshooting

| Issue | Fix |
|---|---|
| HTTP 500 on chat | Check `backend/.env` — use a real API key or leave it empty for demo mode |
| Empty RAG results | Run `python ingest.py` from `backend/` |
| Port 5173 in use | Vite picks the next free port; check the terminal output |
| Qdrant lock error | Stop duplicate backend processes (`pkill -f uvicorn`); only one instance should use `qdrant_storage/` |

## License

This project is licensed under the [MIT License](LICENSE).
