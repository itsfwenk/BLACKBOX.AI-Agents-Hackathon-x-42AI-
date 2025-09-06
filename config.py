"""
Configuration settings for the Research Paper Discovery AI Agent
"""
import os

# Try to load dotenv if available, but don't fail if it's not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use environment variables directly
    pass

class Config:
    # API Endpoints
    SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
    ARXIV_API_BASE = "http://export.arxiv.org/api/query"
    CROSSREF_API_BASE = "https://api.crossref.org/works"
    PUBMED_API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    IEEE_API_BASE = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
    SPRINGER_API_BASE = "http://api.springernature.com/meta/v2/json"
    
    # API Keys (optional for most services)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Search Parameters
    MAX_PAPERS_PER_QUERY = 50
    MIN_CITATION_COUNT = 5
    RECENT_YEARS_THRESHOLD = 3  # Papers from last 3 years considered "recent"
    
    # Output Settings
    DEFAULT_OUTPUT_FORMAT = "markdown"
    MAX_ABSTRACT_LENGTH = 500
    
    # Rate Limiting
    API_DELAY_SECONDS = 1
    MAX_RETRIES = 3
    
    # Agent Behavior
    ENABLE_SUMMARIZATION = True
    ENABLE_TREND_ANALYSIS = True
    ENABLE_CITATION_NETWORK = True
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        if cls.ENABLE_SUMMARIZATION and not cls.OPENAI_API_KEY:
            print("Warning: OpenAI API key not found. Summarization features will be limited.")
        
        return True
