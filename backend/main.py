import sys
import os
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from tools import rag_engine

# Add parent directory to path to import agent_graph
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_graph import graph
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(title="AgriCatalogues AI API")

# Allow CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = [] # [{"role": "user", "content": "..."}]

def format_history(history: List[dict]):
    """Convert JSON history to LangChain messages."""
    params = []
    for msg in history:
        if msg["role"] == "user":
            params.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            params.append(AIMessage(content=msg["content"]))
    return params

async def stream_generator(message: str, history: List[dict]):
    """Generator for streaming LangGraph events."""
    try:
        # Prepare inputs
        formatted_history = format_history(history)
        formatted_history.append(HumanMessage(content=message))
        
        inputs = {"messages": formatted_history}
        
        # Stream from Graph
        for event in graph.stream(inputs):
            for key, value in event.items():
                chunk = {}
                
                if key == "Supervisor":
                    if "thought" in value:
                        chunk["type"] = "thought"
                        chunk["content"] = value["thought"]
                        
                    # Check for Final Answer
                    if "messages" in value and value["next"] == "FINISH":
                        chunk["type"] = "answer"
                        chunk["content"] = value["messages"][0].content
                        
                elif key == "Librarian":
                    # Intermediate update
                    if "messages" in value:
                        msg = value["messages"][0].content
                        chunk["type"] = "thought"
                        chunk["content"] = f"📚 Librarian: {msg}"
                        
                elif key == "Analyst":
                    if "messages" in value:
                         msg = value["messages"][0].content
                         chunk["type"] = "thought"
                         chunk["content"] = f"📊 Analyst: {msg}"
                
                if chunk:
                    # SSE Format
                    yield f"data: {json.dumps(chunk)}\n\n"
                    # Small delay to ensure UI updates smoothly (optional)
                    await asyncio.sleep(0.05)

        # Signal Done
        yield "data: [DONE]\n\n"

    except Exception as e:
        err_Chunk = {"type": "error", "content": str(e)}
        yield f"data: {json.dumps(err_Chunk)}\n\n"

@app.get("/documents")
async def get_documents():
    """Returns the list of indexed documents from metadata.json."""
    metadata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.post("/documents/sync")
async def sync_documents():
    """Triggers incremental sync of new PDFs with real-time updates."""
    metadata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "metadata.json")
    
    async def event_generator():
        for status in rag_engine.sync_new_files(metadata_path=metadata_path):
             # Send as a simple text stream or JSON
             yield json.dumps({"status": status}) + "\n"
             await asyncio.sleep(0.01) # Yield control

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(
        stream_generator(request.message, request.history),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
