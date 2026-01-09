from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from research_agent import ResearchAgent
from exceptions import ResearchError, ConfigurationError, AnalysisError
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

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
    max_content_chars: int = None

@app.post("/api/research")
async def start_research(request: ResearchRequest):
    try:
        if not request.topic:
            raise HTTPException(status_code=400, detail="Topic is required")
        
        agent = ResearchAgent(
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            base_url=request.base_url,
            max_content_chars=request.max_content_chars
        )
        
        result = await agent.conduct_research(request.topic)
        return result
    except ConfigurationError as e:
        logger.warning(f"Configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AnalysisError as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except ResearchError as e:
        logger.error(f"Research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
