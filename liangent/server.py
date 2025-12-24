from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from liangent.config import get_settings
import time
from typing import Optional

from liangent.memory.db import init_db, get_db
from liangent.memory.manager import SessionManager
from liangent.core.agent import ContextAgent
from liangent.core.llm import LLMClient

app = FastAPI(title="Liangent Serverless", version="0.2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
# In production, restrict this
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB on startup
@app.on_event("startup")
def on_startup():
    init_db()
    
    # Init default provider if needed
    db = next(get_db())
    try:
        sm = SessionManager(db)
        sm.seed_default_provider(get_settings())
    finally:
        db.close()

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: str = "default_user"
    query: str
    stream: bool = True

def format_duration(seconds: float) -> str:
    ms = int((seconds % 1) * 1000)
    total_seconds = int(seconds)
    minutes = total_seconds // 60
    rem_seconds = total_seconds % 60
    
    parts = []
    if minutes > 0:
        parts.append(f"{minutes}min")
        # Show seconds if minutes > 0 or seconds > 0
    if rem_seconds > 0 or minutes > 0:
        parts.append(f"{rem_seconds}s")
    parts.append(f"{ms}ms")
    
    return " ".join(parts)

def event_generator(agent: ContextAgent, query: str):
    start_time = time.time()
    try:
        # Yield session ID metadata first
        yield "event: meta\n"
        yield f"data: {json.dumps({'session_id': agent.session_id}, ensure_ascii=False)}\n\n"

        usage_stats = {}
        cost_stats = {}
        for event in agent.run(query):
            # Format as SSE
            evt_name = event.get("event", "message")
            
            if evt_name == "usage_stats":
                # Capture for final done event
                content = event.get("content", {})
                usage_stats = content.get("usage", {})
                cost_stats = content.get("cost", {})
                continue
                
            # Remove event key from data payload
            data_payload = {k: v for k, v in event.items() if k != "event"}
            
            yield f"event: {evt_name}\n"
            yield f"data: {json.dumps(data_payload, ensure_ascii=False)}\n\n"
            
        yield "event: done\n"
        duration_str = format_duration(time.time() - start_time)
        yield f"data: {json.dumps({'usage': usage_stats, 'cost': cost_stats, 'duration': duration_str}, ensure_ascii=False)}\n\n"
            
    except Exception as e:
        yield "event: error\n"
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, db = Depends(get_db)):
    sm = SessionManager(db)
    
    # Initialize Agent
    # Note: If no session_id provided, agent/sm handles creating one
    
    # Initialize LLM with default settings (env/config)
    # In a real app, you might want to cache this or pool it
    llm = LLMClient()
    
    agent = ContextAgent(
        llm_client=llm,
        session_manager=sm,
        session_id=req.session_id,
        user_id=req.user_id
    )
    
    if req.stream:
        return StreamingResponse(
            event_generator(agent, req.query),
            media_type="text/event-stream"
        )
    else:
        # Non-streaming mode (just collect final answer)
        # For now, simplistic implementation collecting all events
        results = []
        for event in agent.run(req.query):
            results.append(event)
        return results

@app.get("/health")
def health_check():
    return {"status": "ok"}
