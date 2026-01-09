import os
import asyncio
import aiohttp
import trafilatura
from duckduckgo_search import DDGS
from groq import Groq
from openai import OpenAI
from anthropic import Anthropic
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

class ResearchAgent:
    def __init__(self, provider: str = "groq", api_key: str = None, base_url: str = None, model: str = None):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("GROQ_API_KEY") # Fallback to Env for Groq
        self.base_url = base_url
        self.model = model
        self.client = self._initialize_client()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    def _initialize_client(self):
        """Initializes the appropriate LLM client based on provider."""
        try:
            if self.provider == "groq":
                if not self.api_key:
                    raise ValueError("Groq API Key is missing.")
                self.model = self.model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
                return Groq(api_key=self.api_key)
            
            elif self.provider == "openai":
                if not self.api_key:
                    raise ValueError("OpenAI API Key is missing.")
                self.model = self.model or "gpt-4o"
                return OpenAI(api_key=self.api_key)
            
            elif self.provider == "anthropic":
                if not self.api_key:
                    raise ValueError("Anthropic API Key is missing.")
                self.model = self.model or "claude-3-opus-20240229"
                return Anthropic(api_key=self.api_key)
            
            elif self.provider == "custom":
                if not self.base_url:
                    raise ValueError("Base URL is required for Custom provider.")
                self.model = self.model or "local-model"
                return OpenAI(api_key=self.api_key or "dummy", base_url=self.base_url)
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            print(f"Error initializing client: {e}")
            raise

    async def search(self, query: str, max_results: int = 5):
        """Searches the web for the query securely."""
        print(f"Searching for: {query}")
        try:
            # Run blocking DDGS in a separate thread to prevent freezing
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._search_sync, query, max_results)
        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def _search_sync(self, query: str, max_results: int):
        """Synchronous helper for DDGS"""
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    async def scrape_url(self, session, url):
        """Scrapes a single URL asynchronously with stealth headers."""
        print(f"Scraping: {url}")
        try:
            async with session.get(url, headers=self.headers, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    # Use trafilatura on the HTML content
                    text = trafilatura.extract(html)
                    if not text:
                        # Fallback to simple soup if trafilatura fails to extract
                        soup = BeautifulSoup(html, 'html.parser')
                        text = soup.get_text(separator='\n', strip=True)
                    
                    # Safety Truncation: Limit to ~12k characters per source
                    return {"url": url, "content": text[:12000] if text else ""}
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
        return None

    async def scrape(self, urls: list[str]):
        """Concurrent scraping of multiple URLs."""
        async with aiohttp.ClientSession() as session:
            tasks = [self.scrape_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r]

    async def analyze(self, topic: str, search_results: list, scraped_content: list):
        """Analyzes the gathered information to generate a report."""
        print(f"Analyzing data for topic: {topic} using {self.provider}")
        
        context = ""
        for item in scraped_content:
            context += f"\n--- SOURCE: {item['url']} ---\n{item['content'][:8000]}\n"
        
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
            # Offload blocking LLM calls to thread
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
            return f"Error during analysis: {str(e)}"

    async def conduct_research(self, topic: str):
        """Runs the full research pipeline asynchronously."""
        search_results = await self.search(topic)
        urls = [r['href'] for r in search_results]
        scraped_data = await self.scrape(urls)
        report = await self.analyze(topic, search_results, scraped_data)
        return {
            "topic": topic,
            "search_results": search_results,
            "report": report
        }
