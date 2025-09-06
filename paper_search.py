"""
Paper search and retrieval logic for the Research AI Agent
"""
import requests
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote
import xml.etree.ElementTree as ET
from config import Config

class PaperSearcher:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-AI-Agent/1.0 (mailto:research@example.com)'
        })
    
    def search_papers(self, query: str, max_results: int = None) -> Dict:
        """
        Search for papers using multiple sources and combine results
        """
        if max_results is None:
            max_results = self.config.MAX_PAPERS_PER_QUERY
        
        print(f"🔍 Searching for papers on: '{query}'")
        
        # Search Semantic Scholar
        semantic_papers = self._search_semantic_scholar(query, max_results)
        
        # Search arXiv
        arxiv_papers = self._search_arxiv(query, max_results // 2)
        
        # Combine and deduplicate results
        all_papers = self._combine_and_deduplicate(semantic_papers, arxiv_papers)
        
        # Analyze and categorize papers
        analysis = self._analyze_papers(all_papers, query)
        
        return {
            'query': query,
            'total_papers': len(all_papers),
            'papers': all_papers,
            'analysis': analysis,
            'search_timestamp': datetime.now().isoformat()
        }
    
    def _search_semantic_scholar(self, query: str, limit: int) -> List[Dict]:
        """Search Semantic Scholar API"""
        try:
            url = f"{self.config.SEMANTIC_SCHOLAR_API_BASE}/paper/search"
            params = {
                'query': query,
                'limit': limit,
                'fields': 'paperId,title,authors,year,citationCount,abstract,url,venue,publicationDate,referenceCount,influentialCitationCount'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for paper in data.get('data', []):
                papers.append({
                    'id': paper.get('paperId'),
                    'title': paper.get('title', 'Unknown Title'),
                    'authors': [author.get('name', 'Unknown') for author in paper.get('authors', [])],
                    'year': paper.get('year'),
                    'citation_count': paper.get('citationCount', 0),
                    'abstract': paper.get('abstract', ''),
                    'url': paper.get('url'),
                    'venue': paper.get('venue'),
                    'publication_date': paper.get('publicationDate'),
                    'reference_count': paper.get('referenceCount', 0),
                    'influential_citation_count': paper.get('influentialCitationCount', 0),
                    'source': 'Semantic Scholar'
                })
            
            print(f"✅ Found {len(papers)} papers from Semantic Scholar")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching Semantic Scholar: {e}")
            return []
    
    def _search_arxiv(self, query: str, limit: int) -> List[Dict]:
        """Search arXiv API"""
        try:
            # Format query for arXiv
            formatted_query = quote(f'all:{query}')
            url = f"{self.config.ARXIV_API_BASE}?search_query={formatted_query}&start=0&max_results={limit}&sortBy=relevance&sortOrder=descending"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            papers = []
            
            # Define namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                published = entry.find('atom:published', ns)
                authors = entry.findall('atom:author', ns)
                
                # Extract arXiv ID from the ID field
                id_elem = entry.find('atom:id', ns)
                arxiv_id = id_elem.text.split('/')[-1] if id_elem is not None else 'unknown'
                
                # Parse publication date
                pub_date = None
                year = None
                if published is not None:
                    try:
                        pub_date = published.text
                        year = int(pub_date[:4])
                    except:
                        pass
                
                papers.append({
                    'id': f"arxiv:{arxiv_id}",
                    'title': title.text.strip() if title is not None else 'Unknown Title',
                    'authors': [author.find('atom:name', ns).text for author in authors if author.find('atom:name', ns) is not None],
                    'year': year,
                    'citation_count': 0,  # arXiv doesn't provide citation counts
                    'abstract': summary.text.strip() if summary is not None else '',
                    'url': f"https://arxiv.org/abs/{arxiv_id}",
                    'venue': 'arXiv',
                    'publication_date': pub_date,
                    'reference_count': 0,
                    'influential_citation_count': 0,
                    'source': 'arXiv'
                })
            
            print(f"✅ Found {len(papers)} papers from arXiv")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching arXiv: {e}")
            return []
    
    def _combine_and_deduplicate(self, *paper_lists) -> List[Dict]:
        """Combine paper lists and remove duplicates"""
        all_papers = []
        seen_titles = set()
        
        for paper_list in paper_lists:
            for paper in paper_list:
                title_normalized = paper['title'].lower().strip()
                if title_normalized not in seen_titles:
                    seen_titles.add(title_normalized)
                    all_papers.append(paper)
        
        return all_papers
    
    def _analyze_papers(self, papers: List[Dict], query: str) -> Dict:
        """Analyze papers to identify trends and state-of-the-art"""
        if not papers:
            return {'error': 'No papers found for analysis'}
        
        # Sort by citation count (most cited first)
        most_cited = sorted([p for p in papers if p['citation_count'] > 0], 
                           key=lambda x: x['citation_count'], reverse=True)[:10]
        
        # Sort by recency (most recent first)
        current_year = datetime.now().year
        recent_threshold = current_year - self.config.RECENT_YEARS_THRESHOLD
        recent_papers = sorted([p for p in papers if p['year'] and p['year'] >= recent_threshold], 
                              key=lambda x: x['year'] or 0, reverse=True)[:10]
        
        # Identify highly influential papers
        influential = sorted([p for p in papers if p['influential_citation_count'] > 0], 
                            key=lambda x: x['influential_citation_count'], reverse=True)[:5]
        
        # Venue analysis
        venues = {}
        for paper in papers:
            venue = paper.get('venue', 'Unknown')
            if venue and venue != 'Unknown':
                venues[venue] = venues.get(venue, 0) + 1
        
        top_venues = sorted(venues.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Year distribution
        year_dist = {}
        for paper in papers:
            year = paper.get('year')
            if year:
                year_dist[year] = year_dist.get(year, 0) + 1
        
        return {
            'most_cited': most_cited,
            'recent_papers': recent_papers,
            'influential_papers': influential,
            'top_venues': top_venues,
            'year_distribution': dict(sorted(year_dist.items(), reverse=True)),
            'total_citations': sum(p['citation_count'] for p in papers),
            'average_citations': sum(p['citation_count'] for p in papers) / len(papers) if papers else 0
        }
    
    def get_paper_details(self, paper_id: str, source: str = 'semantic_scholar') -> Optional[Dict]:
        """Get detailed information about a specific paper"""
        if source == 'semantic_scholar':
            return self._get_semantic_scholar_details(paper_id)
        elif source == 'arxiv':
            return self._get_arxiv_details(paper_id)
        return None
    
    def _get_semantic_scholar_details(self, paper_id: str) -> Optional[Dict]:
        """Get detailed paper information from Semantic Scholar"""
        try:
            url = f"{self.config.SEMANTIC_SCHOLAR_API_BASE}/paper/{paper_id}"
            params = {
                'fields': 'paperId,title,authors,year,citationCount,abstract,url,venue,publicationDate,references,citations,tldr'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Error getting paper details: {e}")
            return None
