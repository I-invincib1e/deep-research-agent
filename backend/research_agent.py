import os
import asyncio
import aiohttp
import logging
import trafilatura
from duckduckgo_search import DDGS
from groq import Groq
from openai import OpenAI
from anthropic import Anthropic
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from exceptions import ResearchError, SearchError, ScrapeError, AnalysisError, ConfigurationError

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ResearchAgent")


def redact_key(key: str) -> str:
    """Redact API key for safe logging (show first 4 chars only)."""
    if not key or len(key) < 8:
        return "****"
    return f"{key[:4]}...{key[-2:]}"


def estimate_tokens(text: str) -> int:
    """Estimate token count using character heuristic (~4 chars per token)."""
    return len(text) // 4


class ResearchAgent:
    # Configuration constants
    MAX_CONCURRENT_SCRAPES = 5
    SCRAPE_DELAY_SECONDS = 0.5
    DEFAULT_MAX_CONTENT_CHARS = 12000
    MAX_CONTEXT_TOKENS = 6000  # Safe limit for most models

    def __init__(
        self, 
        provider: str = "groq", 
        api_key: str = None, 
        base_url: str = None, 
        model: str = None,
        max_content_chars: int = None
    ):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")  # Fallback to Env for Groq
        self.base_url = base_url
        self.model = model
        self.max_content_chars = max_content_chars or self.DEFAULT_MAX_CONTENT_CHARS
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
                    raise ConfigurationError("Groq API Key is missing. Set GROQ_API_KEY in .env or provide via settings.")
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
                if not self.api_key:
                    logger.warning("No API key provided for custom provider. Some endpoints may require one.")
                self.model = self.model or "local-model"
                return OpenAI(api_key=self.api_key or "not-needed", base_url=self.base_url)
            
            else:
                raise ConfigurationError(f"Unsupported provider: {self.provider}")
        except ConfigurationError:
            raise
        except Exception as e:
            # Redact any potential key leaks in error messages
            error_msg = str(e)
            if self.api_key and self.api_key in error_msg:
                error_msg = error_msg.replace(self.api_key, redact_key(self.api_key))
            logger.error(f"Client initialization failed: {error_msg}")
            raise ConfigurationError(f"Failed to initialize {self.provider} client: {error_msg}")

    async def search(self, query: str, max_results: int = 5):
        """Searches the web for the query with error handling."""
        logger.info(f"🔍 Searching for: {query}")
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self._search_sync, query, max_results)
            logger.info(f"✅ Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            # Return empty list instead of crashing - allows graceful degradation
            return []

    def _search_sync(self, query: str, max_results: int):
        """Synchronous helper for DDGS with retry logic."""
        try:
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}. Returning empty results.")
            return []

    async def scrape_url(self, session, url):
        """Scrapes a single URL with rate limiting and semaphore."""
        async with self._semaphore:
            logger.debug(f"📄 Scraping: {url}")
            try:
                # Rate limiting delay
                await asyncio.sleep(self.SCRAPE_DELAY_SECONDS)
                
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        html = await response.text()
                        text = trafilatura.extract(html)
                        if not text:
                            soup = BeautifulSoup(html, 'html.parser')
                            text = soup.get_text(separator='\n', strip=True)
                        
                        # Configurable truncation
                        content = text[:self.max_content_chars] if text else ""
                        logger.debug(f"✅ Scraped {len(content)} chars from {url}")
                        return {"url": url, "content": content}
                    else:
                        logger.warning(f"⚠️ HTTP {response.status} for {url}")
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Timeout scraping {url}")
            except Exception as e:
                logger.debug(f"❌ Failed to scrape {url}: {e}")
            return None

    async def scrape(self, urls: list[str]):
        """Concurrent scraping with progress tracking."""
        logger.info(f"📥 Starting concurrent scrape of {len(urls)} URLs (max {self.MAX_CONCURRENT_SCRAPES} parallel)")
        async with aiohttp.ClientSession() as session:
            tasks = [self.scrape_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            successful = [r for r in results if r]
            logger.info(f"✅ Successfully scraped {len(successful)}/{len(urls)} URLs")
            return successful

    async def analyze(self, topic: str, search_results: list, scraped_content: list):
        """Analyzes content with token management and proper error handling."""
        logger.info(f"🧠 Analyzing data for topic: {topic} using {self.provider}")
        
        # Build context with token awareness
        context = ""
        total_tokens = 0
        sources_used = 0
        
        for item in scraped_content:
            item_text = f"\n--- SOURCE: {item['url']} ---\n{item['content'][:8000]}\n"
            item_tokens = estimate_tokens(item_text)
            
            if total_tokens + item_tokens > self.MAX_CONTEXT_TOKENS:
                logger.warning(f"⚠️ Token limit reached. Using {sources_used} of {len(scraped_content)} sources.")
                break
            
            context += item_text
            total_tokens += item_tokens
            sources_used += 1
        
        logger.info(f"📊 Context: ~{total_tokens} tokens from {sources_used} sources")
        
        system_prompt = (
            "You are a 'Deep Research Agent'. Your goal is to produce a professional, structured intelligence report "
            "based on the provided web search results and scraped content. "
            "Focus on depth, clarity, and actionable insights. "
            "Format the output in clean Markdown."
        )
        
        user_prompt = (
            f"Topic: {topic}\n\n"
            f"Search Results Summary:\n{search_results}\n\n"
            f"Scraped Content:\n{context}\n\n"
            "Please generate a comprehensive intelligence report on the topic."
        )

        try:
            loop = asyncio.get_event_loop()
            if self.provider == "anthropic":
                response = await loop.run_in_executor(
                    None, 
                    lambda: self.client.messages.create(
                        model=self.model,
                        max_tokens=2048,
                        temperature=0.7,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}]
                    )
                )
                return response.content[0].text
            else:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        model=self.model,
                        temperature=0.7,
                        max_tokens=2048
                    )
                )
                return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            # Redact API key from error messages
            if self.api_key and self.api_key in error_msg:
                error_msg = error_msg.replace(self.api_key, redact_key(self.api_key))
            logger.error(f"❌ Analysis failed: {error_msg}")
            raise AnalysisError(f"LLM analysis failed: {error_msg}")

    async def conduct_research(self, topic: str):
        """Runs the full research pipeline with comprehensive error handling."""
        logger.info(f"🚀 Starting research on: {topic}")
        
        try:
            search_results = await self.search(topic)
            
            if not search_results:
                logger.warning("⚠️ No search results found. Generating report with limited context.")
                return {
                    "topic": topic,
                    "search_results": [],
                    "report": f"# Research Report: {topic}\n\nNo search results were found for this topic. Please try a different query or check your internet connection."
                }
            
            urls = [r['href'] for r in search_results]
            scraped_data = await self.scrape(urls)
            
            if not scraped_data:
                logger.warning("⚠️ No content scraped. Generating report from search summaries only.")
            
            report = await self.analyze(topic, search_results, scraped_data)
            
            logger.info(f"✅ Research complete for: {topic}")
            return {
                "topic": topic,
                "search_results": search_results,
                "report": report
            }
        except AnalysisError:
            raise
        except Exception as e:
            logger.error(f"❌ Research pipeline failed: {e}")
            raise ResearchError(f"Research failed: {str(e)}")
