from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import UUID

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from system_prompt import SYSTEM_PROMPT

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("CHAZZ_DATA_DIR", ROOT / "data" / "sessions"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")
MAX_MESSAGES = 40

app = FastAPI(title="Chazz", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


class ChatRequest(BaseModel):
    session_id: UUID
    message: str = Field(min_length=1, max_length=12_000)


class EditRequest(BaseModel):
    session_id: UUID
    message_id: str
    content: str = Field(min_length=1, max_length=12_000)


class ClearRequest(BaseModel):
    session_id: UUID


def session_path(session_id: UUID) -> Path:
    return DATA_DIR / f"{session_id}.json"


def load_history(session_id: UUID) -> list[dict[str, str]]:
    path = session_path(session_id)
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        messages = value.get("messages", [])
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")
        return messages
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Saved conversation could not be read") from exc


def save_history(session_id: UUID, messages: list[dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = session_path(session_id)
    temporary = path.with_suffix(".json.tmp")
    payload = {"session_id": str(session_id), "updated_at": datetime.now(timezone.utc).isoformat(), "messages": messages}
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


async def ask_ollama(messages: list[dict[str, str]]) -> str:
    request_messages = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=5.0)) as client:
            response = await client.post(
                f"{OLLAMA_URL.rstrip('/')}/api/chat",
                json={"model": OLLAMA_MODEL, "messages": request_messages, "stream": False},
            )
            response.raise_for_status()
            reply = response.json().get("message", {}).get("content", "").strip()
            if not reply:
                raise HTTPException(status_code=502, detail="Ollama returned an empty reply")
            return reply
    except httpx.ConnectError as exc:
        raise HTTPException(status_code=503, detail="Cannot reach Ollama. Start Ollama and try again.") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama request failed ({exc.response.status_code})") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Ollama request failed") from exc


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "model": OLLAMA_MODEL}


@app.get("/api/history/{session_id}")
async def history(session_id: UUID) -> dict[str, object]:
    messages = load_history(session_id)
    return {"session_id": str(session_id), "messages": messages}


async def generate(session_id: UUID, messages: list[dict[str, str]]) -> dict[str, object]:
    reply = await ask_ollama(messages)
    messages.append({"id": os.urandom(8).hex(), "role": "assistant", "content": reply})
    messages = messages[-MAX_MESSAGES:]
    save_history(session_id, messages)
    return {"reply": reply, "messages": messages}


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict[str, object]:
    messages = load_history(request.session_id)
    messages.append({"id": os.urandom(8).hex(), "role": "user", "content": request.message.strip()})
    return await generate(request.session_id, messages)


@app.post("/api/retry")
async def retry(request: ClearRequest) -> dict[str, object]:
    messages = load_history(request.session_id)
    if not messages or messages[-1]["role"] != "assistant":
        raise HTTPException(status_code=409, detail="There is no assistant reply to retry")
    messages.pop()
    if not messages or messages[-1]["role"] != "user":
        raise HTTPException(status_code=409, detail="The last user message is missing")
    return await generate(request.session_id, messages)


@app.post("/api/edit")
async def edit(request: EditRequest) -> dict[str, object]:
    messages = load_history(request.session_id)
    index = next((i for i, message in enumerate(messages) if message["id"] == request.message_id), None)
    if index is None or messages[index]["role"] != "user":
        raise HTTPException(status_code=404, detail="User message not found")
    messages = messages[:index + 1]
    messages[-1]["content"] = request.content.strip()
    save_history(request.session_id, messages)
    return await generate(request.session_id, messages)


@app.delete("/api/history/{session_id}")
async def clear_history(session_id: UUID) -> dict[str, str]:
    path = session_path(session_id)
    path.unlink(missing_ok=True)
    return {"status": "cleared"}
