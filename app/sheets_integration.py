"""
Google Sheets integration for market trend tracking and data analysis.
Automatically logs listings, prices, and market insights.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass

try:
    import gspread
    from google.auth.exceptions import GoogleAuthError
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    gspread = None
    GoogleAuthError = Exception
    Credentials = None

logger = logging.getLogger(__name__)

@dataclass
class MarketTrend:
    """Market trend data"""
    product_name: str
    avg_price: float
    min_price: float
    max_price: float
    listing_count: int
    trend_direction: str  # "up", "down", "stable"
    confidence: float

class SheetsManager:
    """Google Sheets manager for market data tracking"""
    
    def __init__(self, credentials_path: Optional[str] = None, spreadsheet_name: str = "Vinted Market Tracker"):
        if not SHEETS_AVAILABLE:
            raise ImportError("Google Sheets dependencies not installed. Run: pip install gspread google-auth")
        
        self.credentials_path = credentials_path or os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "credentials.json")
        self.spreadsheet_name = spreadsheet_name
        self.spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.client = None
        self.spreadsheet = None
        
        # Sheet configurations
        self.sheets_config = {
            "listings": {
                "headers": [
                    "Timestamp", "Product", "Title", "Price", "Currency", "Condition", 
                    "Brand", "Seller_Rating", "URL", "AI_Match", "AI_Confidence", "Deal_Quality"
                ]
            },
            "market_trends": {
                "headers": [
                    "Date", "Product", "Avg_Price", "Min_Price", "Max_Price", 
                    "Listing_Count", "Trend", "Confidence"
                ]
            },
            "notifications": {
                "headers": [
                    "Timestamp", "Product", "Title", "Price", "Reason", "Notified", "URL"
                ]
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize Google Sheets connection"""
        try:
            # Load credentials
            if not os.path.exists(self.credentials_path):
                logger.error(f"Google credentials file not found: {self.credentials_path}")
                return False
            
            # Authenticate
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(self.credentials_path, scopes=scope)
            self.client = gspread.authorize(creds)
            
            # Open or create spreadsheet
            try:
                if self.spreadsheet_id:
                    # Use specific spreadsheet ID if provided
                    self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                    logger.info(f"Opened spreadsheet by ID: {self.spreadsheet_id}")
                else:
                    # Open by name or create new
                    try:
                        self.spreadsheet = self.client.open(self.spreadsheet_name)
                        logger.info(f"Opened existing spreadsheet: {self.spreadsheet_name}")
                    except gspread.SpreadsheetNotFound:
                        self.spreadsheet = self.client.create(self.spreadsheet_name)
                        logger.info(f"Created new spreadsheet: {self.spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                logger.error(f"Spreadsheet not found with ID: {self.spreadsheet_id}")
                return False
            
            # Initialize sheets
            await self._setup_sheets()
            
            logger.info("Google Sheets integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            return False
    
    async def _setup_sheets(self):
        """Setup required sheets with headers"""
        for sheet_name, config in self.sheets_config.items():
            try:
                # Try to get existing sheet
                try:
                    sheet = self.spreadsheet.worksheet(sheet_name)
                    logger.debug(f"Found existing sheet: {sheet_name}")
                except gspread.WorksheetNotFound:
                    # Create new sheet
                    sheet = self.spreadsheet.add_worksheet(
                        title=sheet_name,
                        rows=1000,
                        cols=len(config["headers"])
                    )
                    logger.info(f"Created new sheet: {sheet_name}")
                
                # Set headers if sheet is empty
                if not sheet.get_all_values():
                    sheet.append_row(config["headers"])
                    logger.debug(f"Added headers to sheet: {sheet_name}")
                    
            except Exception as e:
                logger.error(f"Failed to setup sheet {sheet_name}: {e}")
    
    async def log_listing(self, listing: Dict[str, Any], watch_name: str, 
                         ai_analysis: Optional[Dict] = None, notified: bool = False):
        """Log a listing to the sheets"""
        if not self.spreadsheet:
            logger.warning("Sheets not initialized, skipping log")
            return
        
        try:
            # Prepare listing data
            timestamp = datetime.now().isoformat()
            row_data = [
                timestamp,
                watch_name,
                listing.get('title', 'Unknown'),
                listing.get('price_amount', 0),
                listing.get('price_currency', 'EUR'),
                listing.get('condition', 'Unknown'),
                listing.get('brand', 'Unknown'),
                listing.get('seller_rating', 0),
                listing.get('url', ''),
                ai_analysis.get('is_match', False) if ai_analysis else False,
                ai_analysis.get('confidence', 0) if ai_analysis else 0,
                ai_analysis.get('deal_quality', 'unknown') if ai_analysis else 'unknown'
            ]
            
            # Log to listings sheet
            listings_sheet = self.spreadsheet.worksheet("listings")
            listings_sheet.append_row(row_data)
            
            # Log to notifications sheet if notified
            if notified:
                notification_data = [
                    timestamp,
                    watch_name,
                    listing.get('title', 'Unknown'),
                    listing.get('price_amount', 0),
                    ai_analysis.get('reasoning', 'No reason') if ai_analysis else 'Basic match',
                    True,
                    listing.get('url', '')
                ]
                
                notifications_sheet = self.spreadsheet.worksheet("notifications")
                notifications_sheet.append_row(notification_data)
            
            logger.debug(f"Logged listing to sheets: {listing.get('title', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to log listing to sheets: {e}")
    
    async def update_market_trends(self, trends: List[MarketTrend]):
        """Update market trends data"""
        if not self.spreadsheet:
            logger.warning("Sheets not initialized, skipping trends update")
            return
        
        try:
            trends_sheet = self.spreadsheet.worksheet("market_trends")
            
            # Clear existing data (keep headers)
            trends_sheet.clear()
            trends_sheet.append_row(self.sheets_config["market_trends"]["headers"])
            
            # Add trend data
            for trend in trends:
                row_data = [
                    datetime.now().strftime("%Y-%m-%d"),
                    trend.product_name,
                    trend.avg_price,
                    trend.min_price,
                    trend.max_price,
                    trend.listing_count,
                    trend.trend_direction,
                    trend.confidence
                ]
                trends_sheet.append_row(row_data)
            
            logger.info(f"Updated market trends: {len(trends)} products")
            
        except Exception as e:
            logger.error(f"Failed to update market trends: {e}")
    
    async def get_market_data(self, product_name: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get market data for a product from the last N days"""
        if not self.spreadsheet:
            return None
        
        try:
            listings_sheet = self.spreadsheet.worksheet("listings")
            all_records = listings_sheet.get_all_records()
            
            # Filter by product and date
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_records = []
            
            for record in all_records:
                try:
                    record_date = datetime.fromisoformat(record['Timestamp'])
                    if (record_date >= cutoff_date and 
                        product_name.lower() in record['Product'].lower()):
                        filtered_records.append(record)
                except (ValueError, KeyError):
                    continue
            
            if not filtered_records:
                return None
            
            # Calculate statistics
            prices = [float(r['Price']) for r in filtered_records if r['Price']]
            
            return {
                "product_name": product_name,
                "listing_count": len(filtered_records),
                "avg_price": sum(prices) / len(prices) if prices else 0,
                "min_price": min(prices) if prices else 0,
                "max_price": max(prices) if prices else 0,
                "recent_listings": filtered_records[-10:],  # Last 10 listings
                "date_range": f"{cutoff_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}"
            }
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return None
    
    def get_spreadsheet_url(self) -> Optional[str]:
        """Get the URL of the spreadsheet"""
        if self.spreadsheet:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet.id}"
        return None

class MarketAnalyzer:
    """Analyze market trends from collected data"""
    
    def __init__(self, sheets_manager: SheetsManager):
        self.sheets_manager = sheets_manager
    
    async def analyze_trends(self, watch_configs: List[Dict[str, Any]]) -> List[MarketTrend]:
        """Analyze market trends for all watched products"""
        trends = []
        
        for watch in watch_configs:
            product_name = watch.get('name', 'Unknown')
            
            # Get recent market data
            current_data = await self.sheets_manager.get_market_data(product_name, days=7)
            historical_data = await self.sheets_manager.get_market_data(product_name, days=30)
            
            if not current_data or not historical_data:
                continue
            
            # Calculate trend
            trend_direction = "stable"
            confidence = 0.5
            
            if (current_data['avg_price'] > historical_data['avg_price'] * 1.1):
                trend_direction = "up"
                confidence = min(0.9, (current_data['avg_price'] / historical_data['avg_price'] - 1) * 2)
            elif (current_data['avg_price'] < historical_data['avg_price'] * 0.9):
                trend_direction = "down"
                confidence = min(0.9, (1 - current_data['avg_price'] / historical_data['avg_price']) * 2)
            
            trend = MarketTrend(
                product_name=product_name,
                avg_price=current_data['avg_price'],
                min_price=current_data['min_price'],
                max_price=current_data['max_price'],
                listing_count=current_data['listing_count'],
                trend_direction=trend_direction,
                confidence=confidence
            )
            
            trends.append(trend)
        
        return trends
    
    async def get_deal_recommendations(self, watch_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get deal recommendations based on market analysis"""
        recommendations = []
        
        for watch in watch_configs:
            product_name = watch.get('name', 'Unknown')
            max_price = watch.get('max_price', 999999)
            
            market_data = await self.sheets_manager.get_market_data(product_name, days=30)
            
            if not market_data:
                continue
            
            # Calculate recommendation
            avg_price = market_data['avg_price']
            min_price = market_data['min_price']
            
            # Recommend if current max_price is above average
            if max_price > avg_price * 1.2:
                recommended_price = avg_price * 0.9  # 10% below average
                
                recommendations.append({
                    "product": product_name,
                    "current_max_price": max_price,
                    "recommended_max_price": recommended_price,
                    "market_avg": avg_price,
                    "market_min": min_price,
                    "potential_savings": max_price - recommended_price,
                    "reasoning": f"Market average is {avg_price:.2f}, consider lowering max price for better deals"
                })
        
        return recommendations

# Factory function
async def create_sheets_manager(credentials_path: Optional[str] = None, 
                              spreadsheet_name: str = "Vinted Market Tracker") -> Optional[SheetsManager]:
    """Create and initialize sheets manager"""
    if not SHEETS_AVAILABLE:
        logger.warning("Google Sheets integration not available (missing dependencies)")
        return None
    
    # Check if Google Sheets is enabled
    if not os.getenv("GOOGLE_SHEETS_ENABLED", "false").lower() == "true":
        logger.info("Google Sheets integration disabled in config")
        return None
    
    manager = SheetsManager(credentials_path, spreadsheet_name)
    
    if await manager.initialize():
        return manager
    else:
        logger.error("Failed to initialize Google Sheets manager")
        return None
