from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from research_agent import ResearchAgent
import uvicorn
import os

app = FastAPI(title="Deep Research Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    topic: str
    provider: str = "groq"
    api_key: str = None
    model: str = None
    base_url: str = None

@app.post("/api/research")
async def start_research(request: ResearchRequest):
    try:
        if not request.topic:
            raise HTTPException(status_code=400, detail="Topic is required")
        
        # Initialize agent per request to handle dynamic keys/configs
        agent = ResearchAgent(
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            base_url=request.base_url
        )
        
        result = agent.conduct_research(request.topic)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
