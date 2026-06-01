from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from vendor_admin_agents.orchestrator import orchestrate
import asyncio
import json

router = APIRouter()


class HistoryMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class QueryRequest(BaseModel):
    query: str
    top_k: int = 3
    history: Optional[List[HistoryMessage]] = []


@router.post("/query")
async def query_rag(request: QueryRequest):
    history = [{"role": m.role, "content": m.content} for m in (request.history or [])]
    queue = asyncio.Queue()

    async def run_orchestrator():
        try:
            result = await orchestrate(request.query, top_k=request.top_k, history=history, stream_queue=queue)
            await queue.put({"type": "result", "payload": result})
        except Exception as e:
            await queue.put({"type": "error", "error": str(e)})

    # Start the orchestrator logic as a background task
    asyncio.create_task(run_orchestrator())

    async def event_generator():
        while True:
            msg = await queue.get()
            if msg.get("type") in ["result", "error"]:
                yield f"data: {json.dumps(msg)}\n\n"
                break
            # Otherwise yield it as a standard log event
            yield f"data: {json.dumps(msg)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")