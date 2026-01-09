"""Custom exceptions for the Research Agent."""

class ResearchError(Exception):
    """Base exception for research-related errors."""
    pass

class SearchError(ResearchError):
    """Error during web search."""
    pass

class ScrapeError(ResearchError):
    """Error during content scraping."""
    pass

class AnalysisError(ResearchError):
    """Error during LLM analysis."""
    pass

class ConfigurationError(ResearchError):
    """Error in agent configuration (e.g., missing API key)."""
    pass
