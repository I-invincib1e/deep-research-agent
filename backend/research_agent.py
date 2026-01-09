import os
import requests
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
                # Custom usually follows OpenAI format
                return OpenAI(api_key=self.api_key or "dummy", base_url=self.base_url)
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            print(f"Error initializing client: {e}")
            raise

    def search(self, query: str, max_results: int = 5):
        """Searches the web for the query."""
        print(f"Searching for: {query}")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results

    def scrape(self, urls: list[str]):
        """Scrapes content from the provided URLs."""
        docs = []
        for url in urls:
            print(f"Scraping: {url}")
            try:
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    text = trafilatura.extract(downloaded)
                    if text:
                        docs.append({"url": url, "content": text})
                else:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.content, 'html.parser')
                        text = soup.get_text(separator='\n', strip=True)
                        docs.append({"url": url, "content": text[:10000]})
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")
        return docs

    def analyze(self, topic: str, search_results: list, scraped_content: list):
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
            if self.provider == "anthropic":
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return message.content[0].text
            else:
                # OpenAI / Groq / Custom share similar API
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.model,
                    temperature=0.7,
                    max_tokens=2048
                )
                return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error during analysis: {str(e)}"

    def conduct_research(self, topic: str):
        """Runs the full research pipeline."""
        search_results = self.search(topic)
        urls = [r['href'] for r in search_results]
        scraped_data = self.scrape(urls)
        report = self.analyze(topic, search_results, scraped_data)
        return {
            "topic": topic,
            "search_results": search_results,
            "report": report
        }
