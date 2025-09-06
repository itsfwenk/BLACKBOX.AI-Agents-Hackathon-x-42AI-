"""
Configuration settings for the Research Paper Discovery AI Agent
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Endpoints
    SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
    ARXIV_API_BASE = "http://export.arxiv.org/api/query"
    CROSSREF_API_BASE = "https://api.crossref.org/works"
    
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
