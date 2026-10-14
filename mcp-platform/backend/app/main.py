from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.db import SessionLocal, engine
from app.models import Conversation, Document, Message
from app.services.mcp_tools import ollama_tools, tool_session
from app.services.ollama import Ollama
from app.services.orchestrator import run_chat
from app.workers.tasks import ingest_document


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    conversation_id: UUID | None = None
    model: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings().upload_path.mkdir(parents=True, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(title="MCP Platform", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(body: ChatRequest):
    model = body.model or get_settings().default_model
    async with SessionLocal() as db:
        if body.conversation_id:
            conversation = await db.get(Conversation, body.conversation_id)
            if conversation is None:
                raise HTTPException(404, "Conversation not found")
        else:
            conversation = Conversation(title=body.message[:80], model=model)
            db.add(conversation)
            await db.flush()
        db.add(
            Message(conversation_id=conversation.id, role="user", content=body.message)
        )
        await db.commit()
        conversation_id = conversation.id
    return StreamingResponse(
        run_chat(conversation_id, model, body.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/conversations")
async def conversations():
    async with SessionLocal() as db:
        rows = (
            await db.scalars(
                select(Conversation).order_by(Conversation.created_at.desc())
            )
        ).all()
        return [
            {
                "id": str(row.id),
                "title": row.title,
                "model": row.model,
                "created_at": row.created_at,
            }
            for row in rows
        ]


@app.get("/api/conversations/{conversation_id}")
async def conversation(conversation_id: UUID):
    async with SessionLocal() as db:
        row = await db.scalar(
            select(Conversation)
            .options(
                selectinload(Conversation.messages).selectinload(Message.tool_calls)
            )
            .where(Conversation.id == conversation_id)
        )
        if row is None:
            raise HTTPException(404, "Conversation not found")
        return {
            "id": str(row.id),
            "title": row.title,
            "model": row.model,
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": str(call.id),
                            "name": call.tool_name,
                            "arguments": call.arguments,
                            "content": call.result,
                            "is_error": call.is_error,
                        }
                        for call in msg.tool_calls
                    ],
                }
                for msg in row.messages
            ],
        }


@app.delete("/api/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: UUID):
    async with SessionLocal() as db:
        row = await db.get(Conversation, conversation_id)
        if row is None:
            raise HTTPException(404, "Conversation not found")
        await db.delete(row)
        await db.commit()


@app.get("/api/models")
async def models():
    try:
        return {
            "models": await Ollama().models(),
            "default": get_settings().default_model,
        }
    except httpx.HTTPError as exc:
        raise HTTPException(503, f"Ollama unavailable: {exc}") from exc


@app.get("/api/mcp-servers")
async def mcp_servers():
    try:
        async with tool_session() as session:
            tools = await ollama_tools(session)
        return [
            {
                "name": "tools",
                "status": "connected",
                "tools": [tool["function"]["name"] for tool in tools],
            }
        ]
    except Exception as exc:
        return [
            {"name": "tools", "status": "disconnected", "error": str(exc), "tools": []}
        ]


@app.post("/api/documents", status_code=202)
async def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    if not filename.lower().endswith((".txt", ".md")):
        raise HTTPException(400, "Only .txt and .md files are supported")
    data = await file.read(2_000_001)
    if len(data) > 2_000_000:
        raise HTTPException(413, "Maximum document size is 2 MB")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "Document must be UTF-8") from exc
    async with SessionLocal() as db:
        row = Document(filename=filename, storage_path="")
        db.add(row)
        await db.flush()
        path = get_settings().upload_path / f"{row.id}.txt"
        path.write_bytes(data)
        row.storage_path = str(path)
        await db.commit()
        document_id = row.id
    job = ingest_document.delay(str(document_id))
    return {"id": str(document_id), "job_id": job.id, "status": "pending"}


@app.get("/api/documents")
async def documents():
    async with SessionLocal() as db:
        rows = (
            await db.scalars(select(Document).order_by(Document.created_at.desc()))
        ).all()
        return [
            {
                "id": str(row.id),
                "filename": row.filename,
                "status": row.status,
                "error": row.error,
            }
            for row in rows
        ]


@app.get("/api/jobs/{job_id}")
async def job(job_id: str):
    result = ingest_document.AsyncResult(job_id)
    return {
        "id": job_id,
        "status": result.status,
        "error": str(result.result) if result.failed() else None,
    }
