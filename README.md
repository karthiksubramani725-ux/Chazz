# Chazz

A small local gaming companion with a FastAPI backend, Ollama (Phi-3 by default),
and a browser chat interface. Conversations are saved as separate local JSON
files per browser session; the server does not keep a shared in-memory history.

## Requirements

- Python 3.10 or newer
- [Ollama](https://ollama.com/) installed and running
- A model pulled locally, for example `ollama pull phi3`

## Run on Windows

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull phi3
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>. Keep Ollama running in the background.

## Run on macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull phi3
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>.

## Configuration

Set `OLLAMA_URL` to use another Ollama host and `OLLAMA_MODEL` to select a model.
Defaults are `http://localhost:11434` and `phi3`. The optional
`CHAZZ_DATA_DIR` changes where per-session conversation files are stored. See
`.env.example`; environment variables must be exported in your shell because
this baseline intentionally does not load a `.env` file.

## Features

- Session-scoped history keyed by a UUID held in browser local storage
- Persistent JSON storage per session, with an atomic file replacement
- Edit a previous user message, retry the latest assistant response, copy replies,
  and clear the current chat
- `/api/health` endpoint and helpful errors when Ollama is unavailable

The local data directory contains private conversation history. It is excluded
from Git. This is a single-user local app and does not include authentication or
network access controls; do not expose it publicly as-is.
