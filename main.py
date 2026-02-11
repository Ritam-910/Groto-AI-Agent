"""
FastAPI backend for AI Agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import uvicorn

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.graph import LangGraphAgent
from models.schemas import ChatRequest, ChatResponse, HealthResponse

agent=None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events"""
    global agent
    
    print(" Starting AI Agent...")
    
    agent = LangGraphAgent(
        model_name="phi3:latest"
    )
    
    health = await agent.health_check()
    if health["ollama_connected"]:
        print(f" Connected to Ollama")
        print(f" Model: {health['model']}")
        if not health.get("model_available"):
            print(f" Warning: Model '{health['model']}' not found. Please run: ollama pull {health['model']}")
    else:
        print(f" Could not connect to Ollama: {health.get('error')}")
        print("   Make sure Ollama is running!")
    
    print(" Storage: In-Memory (conversations reset on restart)")
    
    yield
    
    print(" Shutting down AI Agent...")

app = FastAPI(
    title="AI Agent API",
    description="Intermediate AI Agent powered by Phi3 and Ollama",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Agent API",
        "version": "1.0.0",
        "model": "llama3:latest",
        "endpoints": {
            "chat": "/chat",
            "stream": "/chat/stream",
            "health": "/health",
            "clear": "/chat/clear/{conversation_id}"
        }
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI agent
    
    Args:
        request: Chat request with message and optional conversation_id
    
    Returns:
        Agent's response
    """
    try:
        result = await agent.chat(
            user_message=request.message,
            conversation_id=request.conversation_id
        )
        
        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            timestamp=result["timestamp"],
            metadata=result.get("metadata")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response from the AI agent
    
    Args:
        request: Chat request with message and optional conversation_id
    
    Returns:
        Streaming response
    """
    try:
        async def generate():
            async for chunk in agent.chat_stream(
                user_message=request.message,
                conversation_id=request.conversation_id
            ):
                yield chunk
        
        return StreamingResponse(
            generate(),
            media_type="text/plain"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint
    
    Returns:
        Health status
    """
    health_status = await agent.health_check()
    
    return HealthResponse(
        status=health_status["status"],
        ollama_connected=health_status["ollama_connected"],
        model=health_status["model"]
    )


@app.delete("/chat/clear/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    Clear a conversation from memory
    
    Args:
        conversation_id: ID of conversation to clear
    
    Returns:
        Success status
    """
    success = agent.clear_conversation(conversation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation cleared", "conversation_id": conversation_id}


@app.get("/chat/history/{conversation_id}")
async def get_history(conversation_id: str):
    """
    Get conversation history
    
    Args:
        conversation_id: ID of conversation
    
    Returns:
        Conversation history
    """
    history = agent.get_conversation_history(conversation_id)
    
    if history is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": history
    }




if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True
    )
