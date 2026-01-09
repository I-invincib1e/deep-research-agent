from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from research_agent import ResearchAgent
from exceptions import ResearchError, ConfigurationError, AnalysisError
from pdf_exporter import generate_pdf
import cache
import uvicorn
import logging
import json

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
    messages: list[dict]
    provider: str = "groq"
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    max_content_chars: Optional[int] = None
    use_cache: bool = True

class SourceMetadata(BaseModel):
    id: int
    url: str
    title: str
    domain: str
    snippet: str

class ResearchResponse(BaseModel):
    topic: str
    answer: str
    sources: List[SourceMetadata]
    search_results: list = []
    follow_up_questions: List[str] = []

class PDFExportRequest(BaseModel):
    report: str
    title: str = "Research Report"

@app.post("/api/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """Non-streaming research endpoint"""
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages required")
        
        agent = ResearchAgent(
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            base_url=request.base_url,
            max_content_chars=request.max_content_chars,
            use_cache=request.use_cache
        )
        
        result = await agent.conduct_research(request.messages)
        return ResearchResponse(**result)
        
    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AnalysisError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ResearchError as e:
        logger.error(f"Research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.post("/api/research/stream")
async def start_research_stream(request: ResearchRequest):
    """Streaming endpoint that yields tokens as they're generated"""
    async def generate():
        try:
            agent = ResearchAgent(
                provider=request.provider,
                api_key=request.api_key,
                model=request.model,
                base_url=request.base_url,
                max_content_chars=request.max_content_chars,
                use_cache=request.use_cache
            )
            
            # PHASE 1: Plan
            plan = await agent.generate_plan(request.messages)
            yield f"data: {json.dumps({'type': 'plan_complete', 'plan': plan.__dict__})}\n\n"
            
            # PHASE 2: Research
            evidence = await agent.researcher(plan)
            yield f"data: {json.dumps({'type': 'research_complete', 'evidence_count': len(evidence)})}\n\n"
            
            # PHASE 3: Stream answer tokens
            if agent.provider == "groq":
                stream = agent.client.chat.completions.create(
                    model=agent.model,
                    messages=[
                        {"role": "system", "content": "You are Aura, a research companion. Answer with [1][2][3] citations."},
                        {"role": "user", "content": f"Answer: {plan.main_question}"}
                    ],
                    stream=True,
                    max_tokens=2048
                )
                for chunk in stream:
                    token = chunk.choices[0].delta.content or ""
                    if token:
                        yield f"data: {json.dumps({'type': 'answer_token', 'token': token})}\n\n"
            else:
                answer, sources = await agent.writer(plan, evidence, request.messages)
                yield f"data: {json.dumps({'type': 'answer_full', 'answer': answer})}\n\n"
            
            # Send sources
            sources_metadata = [
                {
                    "id": ev.id,
                    "url": ev.url,
                    "title": ev.title,
                    "domain": ev.source_domain,
                    "snippet": ev.snippet
                }
                for ev in evidence
            ]
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources_metadata})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/api/export/pdf")
async def export_pdf(request: PDFExportRequest):
    try:
        pdf_bytes = generate_pdf(request.report, request.title)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{request.title.replace(" ", "_")}.pdf"'
            }
        )
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@app.delete("/api/cache")
async def clear_cache():
    count = cache.clear_all()
    return {"message": f"Cleared {count} cache entries"}

@app.delete("/api/cache/expired")
async def clear_expired_cache():
    count = cache.clear_expired()
    return {"message": f"Cleared {count} expired cache entries"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
