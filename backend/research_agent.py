import os
import asyncio
import aiohttp
import logging
import trafilatura
import json
import re
from dataclasses import dataclass
from typing import Optional, List
from duckduckgo_search import DDGS
from groq import Groq
from openai import OpenAI
from anthropic import Anthropic
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from exceptions import ResearchError, SearchError, ScrapeError, AnalysisError, ConfigurationError
import cache

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ResearchAgent")

@dataclass
class Evidence:
    """Single piece of evidence from a source"""
    id: int                    # Unique ID for citations [1], [2], etc.
    url: str                   # Source URL
    title: str                 # Page title
    content: str               # Full scraped content (truncated)
    snippet: str               # Short preview (50-100 chars)
    source_domain: str         # Domain name only (e.g., "wikipedia.org")

@dataclass
class ResearchPlan:
    """Structured research plan"""
    main_question: str         # The actual user question
    sub_questions: List[str]   # Breakdown of main question
    search_queries: List[str]  # List of optimized search queries (3-5)
    answer_style: str          # "concise" | "in_depth" | "academic"

def redact_key(key: str) -> str:
    """Redact API key for safe logging (show first 4 chars only)."""
    if not key or len(key) < 8:
        return "****"
    return f"{key[:4]}...{key[-2:]}"

def estimate_tokens(text: str) -> int:
    """Estimate token count using character heuristic (~4 chars per token)."""
    return len(text) // 4

def extract_citations(answer_text: str) -> dict:
    """Extract citation references from answer text."""
    pattern = r'\[(\d+)\]'
    citations = [int(m.group(1)) for m in re.finditer(pattern, answer_text)]
    return {"cited_ids": list(set(citations))}

class ResearchAgent:
    # Configuration constants
    MAX_CONCURRENT_SCRAPES = 5
    SCRAPE_DELAY_SECONDS = 0.5
    DEFAULT_MAX_CONTENT_CHARS = 12000
    MAX_CONTEXT_TOKENS = 6000
    CACHE_TTL_SEARCH = 3600
    CACHE_TTL_SCRAPE = 86400

    def __init__(
        self, 
        provider: str = "groq", 
        api_key: str = None, 
        base_url: str = None, 
        model: str = None,
        max_content_chars: int = None,
        use_cache: bool = True
    ):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = base_url
        self.model = model
        self.max_content_chars = max_content_chars or self.DEFAULT_MAX_CONTENT_CHARS
        self.use_cache = use_cache
        self.client = self._initialize_client()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_SCRAPES)

    def _initialize_client(self):
        """Initializes the appropriate LLM client based on provider."""
        logger.info(f"Initializing {self.provider} client...")
        try:
            if self.provider == "groq":
                if not self.api_key:
                    raise ConfigurationError("Groq API Key is missing.")
                self.model = self.model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
                return Groq(api_key=self.api_key)
            elif self.provider == "openai":
                if not self.api_key:
                    raise ConfigurationError("OpenAI API Key is missing.")
                self.model = self.model or "gpt-4o"
                return OpenAI(api_key=self.api_key)
            elif self.provider == "anthropic":
                if not self.api_key:
                    raise ConfigurationError("Anthropic API Key is missing.")
                self.model = self.model or "claude-3-opus-20240229"
                return Anthropic(api_key=self.api_key)
            elif self.provider == "custom":
                if not self.base_url:
                    raise ConfigurationError("Base URL is required for Custom provider.")
                self.model = self.model or "local-model"
                return OpenAI(api_key=self.api_key or "not-needed", base_url=self.base_url)
            else:
                raise ConfigurationError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"Client initialization failed: {e}")
            raise ConfigurationError(f"Failed to initialize {self.provider} client")

    async def search(self, query: str, max_results: int = 5):
        """Searches the web for the query with caching."""
        cache_key = f"search:{query}:{max_results}"
        if self.use_cache:
            cached = cache.get_cached(cache_key)
            if cached: return cached
        
        logger.info(f"🔍 Searching for: {query}")
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self._search_sync, query, max_results)
            if self.use_cache and results:
                cache.set_cached(cache_key, results, self.CACHE_TTL_SEARCH)
            return results
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []

    def _search_sync(self, query: str, max_results: int):
        try:
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))
        except Exception:
            return []

    async def scrape_url(self, session, url):
        cache_key = f"scrape:{url}"
        if self.use_cache:
            cached = cache.get_cached(cache_key)
            if cached: return cached
        
        async with self._semaphore:
            try:
                await asyncio.sleep(self.SCRAPE_DELAY_SECONDS)
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        html = await response.text()
                        text = trafilatura.extract(html) or BeautifulSoup(html, 'html.parser').get_text(separator='\n', strip=True)
                        content = text[:self.max_content_chars] if text else ""
                        result = {"url": url, "content": content}
                        if self.use_cache and content:
                            cache.set_cached(cache_key, result, self.CACHE_TTL_SCRAPE)
                        return result
            except Exception as e:
                logger.debug(f"❌ Failed to scrape {url}: {e}")
            return None

    async def scrape(self, urls: list[str]):
        logger.info(f"📥 Starting concurrent scrape of {len(urls)} URLs")
        async with aiohttp.ClientSession() as session:
            tasks = [self.scrape_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r]

    async def generate_plan(self, messages: list) -> ResearchPlan:
        """PHASE 1: Generate structured research plan."""
        logger.info("PHASE 1: Generating research plan...")
        last_query = messages[-1]["content"]
        
        prompt = f"""You are a research strategist. Analyze the user's question and create a research plan.

User Question: {last_query}

Return ONLY valid JSON (no markdown, no extra text):
{{
    "main_question": "exact user question here",
    "sub_questions": ["sub-question 1", "sub-question 2", "sub-question 3"],
    "search_queries": ["optimized search 1", "optimized search 2", "optimized search 3"],
    "answer_style": "in_depth"
}}

Rules:
- sub_questions: Break down the main question into 2-4 researchable parts
- search_queries: Create 3-5 varied, specific search queries to find diverse sources
- answer_style: Choose "concise" (short), "in_depth" (detailed), or "academic" (formal)
"""
        try:
            loop = asyncio.get_event_loop()
            if self.provider == "anthropic":
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.messages.create(
                        model=self.model,
                        max_tokens=1024,
                        messages=[{"role": "user", "content": prompt}]
                    )
                )
                text = response.content[0].text
            else:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=1024
                    )
                )
                text = response.choices[0].message.content

            # Clean markdown if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            plan_dict = json.loads(text.strip())
            plan = ResearchPlan(**plan_dict)
            logger.info(f"✅ Plan created with {len(plan.search_queries)} search queries")
            return plan
        except Exception as e:
            logger.warning(f"⚠️ Plan generation failed: {e}. Using fallback.")
            return ResearchPlan(
                main_question=last_query,
                sub_questions=[last_query],
                search_queries=[last_query],
                answer_style="in_depth"
            )

    async def researcher(self, plan: ResearchPlan) -> List[Evidence]:
        """PHASE 2: Execute multi-round research."""
        logger.info("PHASE 2: Executing research...")
        evidence_list = []
        evidence_id = 1
        seen_urls = set()
        
        for query in plan.search_queries:
            logger.info(f"  → Searching: {query}")
            search_results = await self.search(query, max_results=5)
            if not search_results: continue
            
            urls = [r.get("href") for r in search_results if r.get("href")]
            new_urls = [u for u in urls if u not in seen_urls]
            seen_urls.update(new_urls)
            
            if not new_urls: continue

            scraped_data = await self.scrape(new_urls)
            
            for scraped in scraped_data:
                matching_sr = next((sr for sr in search_results if sr.get("href") == scraped["url"]), {})
                try:
                    domain = scraped["url"].split("/")[2]
                except:
                    domain = "unknown"
                
                evidence = Evidence(
                    id=evidence_id,
                    url=scraped["url"],
                    title=matching_sr.get("title", "Untitled"),
                    content=scraped["content"] or "",
                    snippet=matching_sr.get("body", "")[:200],
                    source_domain=domain
                )
                evidence_list.append(evidence)
                logger.debug(f"    Evidence [{evidence_id}] from {domain}")
                evidence_id += 1
        
        logger.info(f"✅ PHASE 2 complete: Collected {len(evidence_list)} sources")
        return evidence_list

    async def writer(self, plan: ResearchPlan, evidence_list: List[Evidence], messages: list) -> tuple:
        """PHASE 3: Write final answer with citations."""
        logger.info("PHASE 3: Writing answer with citations...")
        
        if not evidence_list:
            return "No sources found to answer this question.", []
        
        context_parts = []
        for ev in evidence_list[:8]:
            context_parts.append(f"[{ev.id}] {ev.title} (from {ev.source_domain})\n{ev.content[:1500]}")
        
        context = "\n\n" + "="*80 + "\n\n".join(context_parts)
        
        system_prompt = f"""You are Aura, a research companion like Perplexity.

Your job: Answer the user's question comprehensively using the provided sources.

CITATION RULES (CRITICAL):
- Use [1], [2], [3], etc. to cite sources by their ID
- Place citations immediately after the fact with NO space: [1]
- EVERY factual statement MUST have a citation
- Do NOT say "According to source X" - just cite: [X]
- If citing multiple sources: [1][2]

ANSWER FORMAT:
1. Direct answer: 1-2 sentences answering the main question
2. Sections: 2-4 sections with clear headings
3. Style: Use bullet points for lists
4. Tone: Professional but conversational

Answer Style: {plan.answer_style.upper()}
Question: {plan.main_question}

Now write the answer with proper citations."""
        
        user_prompt = f"""Based on these sources, comprehensively answer:

{plan.main_question}

SOURCES:
{context}

Write the answer now. Remember: citation format is [1], [2], etc. right after each fact. No exceptions."""
        
        try:
            loop = asyncio.get_event_loop()
            if self.provider == "anthropic":
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.messages.create(
                        model=self.model,
                        max_tokens=2048,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}]
                    )
                )
                answer = response.content[0].text
            else:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=2048
                    )
                )
                answer = response.choices[0].message.content
            
            sources_metadata = [
                {
                    "id": ev.id,
                    "url": ev.url,
                    "title": ev.title,
                    "domain": ev.source_domain,
                    "snippet": ev.snippet
                }
                for ev in evidence_list
            ]
            
            logger.info("✅ PHASE 3 complete: Answer generated with citations")
            return answer, sources_metadata
            
        except Exception as e:
            logger.error(f"Writer phase failed: {e}")
            raise AnalysisError(f"Failed to generate answer: {str(e)}")

    async def generate_followup_questions(self, report: str, topic: str) -> list[str]:
        """Generate follow-up research questions based on the report."""
        logger.info(f"🔮 Generating follow-up questions for: {topic}")
        prompt = f"""Based on this research report about "{topic}", suggest 3-5 specific follow-up research questions.
Report: {report[:4000]}
Return ONLY the questions as a numbered list."""

        try:
            loop = asyncio.get_event_loop()
            if self.provider == "anthropic":
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.messages.create(
                        model=self.model, max_tokens=500, temperature=0.7,
                        messages=[{"role": "user", "content": prompt}]
                    )
                )
                text = response.content[0].text
            else:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=self.model, temperature=0.7, max_tokens=500
                    )
                )
                text = response.choices[0].message.content
            
            questions = []
            for line in text.strip().split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    questions.append(line.lstrip('0123456789.)').strip())
            return questions[:5]
        except Exception:
            return []

    async def conduct_research(self, messages: list) -> dict:
        """Main orchestration: Plan → Research → Write"""
        if not messages:
            raise ResearchError("No messages provided")
        
        try:
            # PHASE 1: Plan
            plan = await self.generate_plan(messages)
            
            # PHASE 2: Research
            evidence = await self.researcher(plan)
            
            if not evidence:
                return {
                    "topic": plan.main_question,
                    "answer": "I couldn't find relevant sources to answer your question. Try rephrasing it.",
                    "sources": [],
                    "search_results": [],
                    "follow_up_questions": []
                }
            
            # PHASE 3: Write
            answer, sources_metadata = await self.writer(plan, evidence, messages)
            
            # BONUS: Follow-ups
            follow_ups = await self.generate_followup_questions(answer, plan.main_question)
            
            return {
                "topic": plan.main_question,
                "answer": answer,
                "sources": sources_metadata,
                "search_results": [],
                "follow_up_questions": follow_ups
            }
            
        except Exception as e:
            logger.error(f"Research pipeline failed: {e}")
            raise ResearchError(f"Research failed: {str(e)}")
