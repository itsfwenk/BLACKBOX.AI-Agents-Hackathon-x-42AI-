"""
AI-powered listing analyzer for precise product matching and market analysis.
Supports multiple AI providers: OpenAI, Anthropic, Google Gemini.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    GEMINI = "gemini"

@dataclass
class AnalysisResult:
    """Result of AI analysis"""
    is_match: bool
    confidence: float  # 0.0 to 1.0
    reasoning: str
    market_value: Optional[float] = None
    deal_quality: Optional[str] = None  # "excellent", "good", "fair", "poor"
    tags: List[str] = None

class AIAnalyzer:
    """AI-powered analyzer for Vinted listings"""
    
    def __init__(self, provider: AIProvider = AIProvider.OPENAI):
        self.provider = provider
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API configurations
        self.configs = {
            AIProvider.OPENAI: {
                "api_key": os.getenv("OPENAI_API_KEY") or os.getenv("BLACKBOX_API_KEY"),
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini"  # Cost-effective model
            },
            AIProvider.ANTHROPIC: {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "base_url": "https://api.anthropic.com/v1",
                "model": "claude-3-haiku-20240307"  # Fast and cheap
            },
            AIProvider.GEMINI: {
                "api_key": os.getenv("GEMINI_API_KEY"),
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "model": "gemini-1.5-flash"  # Free tier available
            }
        }
        
        # Validate configuration
        config = self.configs[provider]
        if not config["api_key"]:
            raise ValueError(f"Missing API key for {provider.value}. Set {provider.value.upper()}_API_KEY or BLACKBOX_API_KEY environment variable.")
    
    async def start(self):
        """Initialize the analyzer"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        logger.info(f"AI Analyzer started with {self.provider.value}")
    
    async def stop(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("AI Analyzer stopped")
    
    async def analyze_listing(self, listing: Dict[str, Any], user_query: str, max_price: float) -> AnalysisResult:
        """
        Analyze if a listing matches user requirements using AI
        
        Args:
            listing: Vinted listing data
            user_query: User's search query/requirements
            max_price: Maximum acceptable price
            
        Returns:
            AnalysisResult with match decision and reasoning
        """
        try:
            # Prepare analysis prompt
            prompt = self._create_analysis_prompt(listing, user_query, max_price)
            
            # Get AI response
            response = await self._call_ai_api(prompt)
            
            # Parse response
            result = self._parse_ai_response(response)
            
            logger.debug(f"AI analysis for '{listing.get('title', 'Unknown')}': match={result.is_match}, confidence={result.confidence}")
            
            return result
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # Fallback to basic matching
            return AnalysisResult(
                is_match=True,  # Conservative fallback
                confidence=0.5,
                reasoning=f"AI analysis failed, using fallback: {str(e)}"
            )
    
    def _create_analysis_prompt(self, listing: Dict[str, Any], user_query: str, max_price: float) -> str:
        """Create analysis prompt for AI"""
        
        title = listing.get('title', 'No title')
        description = listing.get('description', 'No description')
        price = listing.get('price_amount', 0)
        currency = listing.get('price_currency', 'EUR')
        condition = listing.get('condition', 'Unknown')
        brand = listing.get('brand', 'Unknown')
        
        prompt = f"""
Analyze this Vinted listing to determine if it matches the user's requirements.

USER REQUIREMENTS:
- Query: "{user_query}"
- Maximum price: {max_price} {currency}

LISTING DETAILS:
- Title: "{title}"
- Description: "{description}"
- Price: {price} {currency}
- Condition: {condition}
- Brand: {brand}

ANALYSIS TASKS:
1. Does this listing match what the user is looking for?
2. Is the price reasonable for this item?
3. What's the quality of this deal?

Consider:
- Exact product match vs similar items
- Price competitiveness 
- Item condition and authenticity
- Seller reliability indicators

Respond in JSON format:
{{
    "is_match": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation",
    "market_value": estimated_market_value_or_null,
    "deal_quality": "excellent/good/fair/poor",
    "tags": ["relevant", "tags", "list"]
}}
"""
        return prompt.strip()
    
    async def _call_ai_api(self, prompt: str) -> str:
        """Call the configured AI API"""
        config = self.configs[self.provider]
        
        if self.provider == AIProvider.OPENAI:
            return await self._call_openai(prompt, config)
        elif self.provider == AIProvider.ANTHROPIC:
            return await self._call_anthropic(prompt, config)
        elif self.provider == AIProvider.GEMINI:
            return await self._call_gemini(prompt, config)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    async def _call_openai(self, prompt: str, config: Dict) -> str:
        """Call BLACKBOX API (OpenAI-compatible)"""
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "blackboxai/openai/gpt-4",  # Use BLACKBOX model
            "messages": [
                {"role": "system", "content": "You are an expert at analyzing marketplace listings. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
        }
        
        # Use BLACKBOX API endpoint
        api_url = "https://api.blackbox.ai/chat/completions"
        
        async with self.session.post(api_url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"BLACKBOX API error: {response.status} - {error_text}")
            
            data = await response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_anthropic(self, prompt: str, config: Dict) -> str:
        """Call Anthropic Claude API"""
        headers = {
            "x-api-key": config['api_key'],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": config["model"],
            "max_tokens": 500,
            "temperature": 0.1,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        async with self.session.post(f"{config['base_url']}/messages",
                                   headers=headers, json=payload) as response:
            if response.status != 200:
                raise Exception(f"Anthropic API error: {response.status}")
            
            data = await response.json()
            return data["content"][0]["text"]
    
    async def _call_gemini(self, prompt: str, config: Dict) -> str:
        """Call Google Gemini API"""
        url = f"{config['base_url']}/models/{config['model']}:generateContent?key={config['api_key']}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 500
            }
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status != 200:
                raise Exception(f"Gemini API error: {response.status}")
            
            data = await response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    
    def _parse_ai_response(self, response: str) -> AnalysisResult:
        """Parse AI response into AnalysisResult"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            data = json.loads(response)
            
            return AnalysisResult(
                is_match=data.get("is_match", False),
                confidence=float(data.get("confidence", 0.0)),
                reasoning=data.get("reasoning", "No reasoning provided"),
                market_value=data.get("market_value"),
                deal_quality=data.get("deal_quality"),
                tags=data.get("tags", [])
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse AI response: {e}")
            # Fallback parsing
            return AnalysisResult(
                is_match="true" in response.lower() or "match" in response.lower(),
                confidence=0.5,
                reasoning=f"Parsed from text: {response[:200]}..."
            )

class SmartFilter:
    """Smart filtering system combining AI analysis with traditional filters"""
    
    def __init__(self, ai_analyzer: AIAnalyzer):
        self.ai_analyzer = ai_analyzer
        self.stats = {
            "total_analyzed": 0,
            "ai_matches": 0,
            "ai_rejects": 0,
            "fallback_used": 0
        }
    
    async def should_notify(self, listing: Dict[str, Any], watch_config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if a listing should trigger a notification
        
        Args:
            listing: Vinted listing data
            watch_config: Watch configuration
            
        Returns:
            (should_notify, reason)
        """
        self.stats["total_analyzed"] += 1
        
        # Basic filters first (price, seller rating, etc.)
        basic_check, basic_reason = self._apply_basic_filters(listing, watch_config)
        if not basic_check:
            return False, f"Basic filter: {basic_reason}"
        
        # AI analysis for precise matching
        try:
            analysis = await self.ai_analyzer.analyze_listing(
                listing=listing,
                user_query=watch_config.get("query", ""),
                max_price=watch_config.get("max_price", 999999)
            )
            
            if analysis.is_match and analysis.confidence >= 0.7:
                self.stats["ai_matches"] += 1
                return True, f"AI match (confidence: {analysis.confidence:.2f}): {analysis.reasoning}"
            else:
                self.stats["ai_rejects"] += 1
                return False, f"AI reject (confidence: {analysis.confidence:.2f}): {analysis.reasoning}"
                
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            self.stats["fallback_used"] += 1
            # Fallback to basic matching
            return True, f"Fallback match (AI failed): {str(e)}"
    
    def _apply_basic_filters(self, listing: Dict[str, Any], watch_config: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply basic non-AI filters"""
        
        # Price filter
        price = listing.get('price_amount', 0)
        max_price = watch_config.get('max_price', 999999)
        if price > max_price:
            return False, f"Price {price} > {max_price}"
        
        min_price = watch_config.get('filters', {}).get('price_from', 0)
        if price < min_price:
            return False, f"Price {price} < {min_price}"
        
        # Seller rating filter
        min_rating = watch_config.get('min_seller_rating')
        if min_rating:
            seller_rating = listing.get('seller_rating', 0)
            if seller_rating < min_rating:
                return False, f"Seller rating {seller_rating} < {min_rating}"
        
        # Seller feedback count filter
        min_feedback = watch_config.get('min_seller_feedback_count')
        if min_feedback:
            feedback_count = listing.get('seller_feedback_count', 0)
            if feedback_count < min_feedback:
                return False, f"Seller feedback {feedback_count} < {min_feedback}"
        
        return True, "Basic filters passed"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get filtering statistics"""
        return self.stats.copy()

# Factory function for easy initialization
async def create_ai_analyzer(provider: str = "openai") -> Optional[AIAnalyzer]:
    """Create and initialize AI analyzer"""
    try:
        provider_enum = AIProvider(provider.lower())
        analyzer = AIAnalyzer(provider_enum)
        await analyzer.start()
        return analyzer
    except Exception as e:
        logger.warning(f"Failed to create AI analyzer ({provider}): {e}")
        return None
