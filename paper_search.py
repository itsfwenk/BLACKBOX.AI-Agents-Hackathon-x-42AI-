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
        
        # Determine search strategy based on query content
        per_source_limit = max(max_results // 4, 10)  # Distribute across 4 main sources, minimum 10 per source
        
        # Search Semantic Scholar (comprehensive academic database)
        semantic_papers = self._search_semantic_scholar(query, per_source_limit)
        
        # Search PubMed (medical and life sciences)
        pubmed_papers = self._search_pubmed(query, per_source_limit)
        
        # Search arXiv (preprints, especially CS/Physics/Math)
        arxiv_papers = self._search_arxiv(query, per_source_limit)
        
        # Search CrossRef (DOI database with broad coverage)
        crossref_papers = self._search_crossref(query, per_source_limit)
        
        # Combine and deduplicate results
        all_papers = self._combine_and_deduplicate(
            semantic_papers, pubmed_papers, arxiv_papers, crossref_papers
        )
        
        # Analyze and categorize papers
        analysis = self._analyze_papers(all_papers, query)
        
        return {
            'query': query,
            'total_papers': len(all_papers),
            'papers': all_papers,
            'analysis': analysis,
            'search_timestamp': datetime.now().isoformat(),
            'sources_used': ['Semantic Scholar', 'PubMed', 'arXiv', 'CrossRef']
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
    
    def _search_pubmed(self, query: str, limit: int) -> List[Dict]:
        """Search PubMed API using NCBI E-utilities"""
        try:
            # Step 1: Search for PMIDs
            search_url = f"{self.config.PUBMED_API_BASE}/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': limit,
                'retmode': 'json',
                'sort': 'relevance'
            }
            
            search_response = self.session.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            pmids = search_data.get('esearchresult', {}).get('idlist', [])
            if not pmids:
                print(f"✅ Found 0 papers from PubMed")
                return []
            
            time.sleep(self.config.API_DELAY_SECONDS)
            
            # Step 2: Fetch detailed information for PMIDs
            fetch_url = f"{self.config.PUBMED_API_BASE}/efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids[:limit]),
                'retmode': 'xml'
            }
            
            fetch_response = self.session.get(fetch_url, params=fetch_params)
            fetch_response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(fetch_response.content)
            papers = []
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    # Extract basic information
                    medline_citation = article.find('.//MedlineCitation')
                    if medline_citation is None:
                        continue
                        
                    pmid_elem = medline_citation.find('.//PMID')
                    pmid = pmid_elem.text if pmid_elem is not None else 'unknown'
                    
                    article_elem = medline_citation.find('.//Article')
                    if article_elem is None:
                        continue
                    
                    # Title - handle multiple text nodes
                    title_elem = article_elem.find('.//ArticleTitle')
                    title = ""
                    if title_elem is not None:
                        # Get all text content including nested elements
                        title = ''.join(title_elem.itertext()).strip()
                    if not title:
                        title = 'Unknown Title'
                    
                    # Authors
                    authors = []
                    author_list = article_elem.find('.//AuthorList')
                    if author_list is not None:
                        for author in author_list.findall('.//Author'):
                            last_name_elem = author.find('.//LastName')
                            first_name_elem = author.find('.//ForeName')
                            initials_elem = author.find('.//Initials')
                            
                            if last_name_elem is not None:
                                name = last_name_elem.text
                                if first_name_elem is not None:
                                    name = f"{first_name_elem.text} {name}"
                                elif initials_elem is not None:
                                    name = f"{initials_elem.text} {name}"
                                authors.append(name)
                    
                    # Abstract - handle multiple AbstractText elements
                    abstract = ""
                    abstract_elem = article_elem.find('.//Abstract')
                    if abstract_elem is not None:
                        abstract_texts = []
                        for abs_text in abstract_elem.findall('.//AbstractText'):
                            if abs_text.text:
                                # Check for label attribute
                                label = abs_text.get('Label', '')
                                text = abs_text.text.strip()
                                if label:
                                    abstract_texts.append(f"{label}: {text}")
                                else:
                                    abstract_texts.append(text)
                        abstract = " ".join(abstract_texts)
                    
                    # Publication date and year
                    pub_date = None
                    year = None
                    pub_date_elem = article_elem.find('.//PubDate')
                    if pub_date_elem is not None:
                        year_elem = pub_date_elem.find('.//Year')
                        if year_elem is not None:
                            try:
                                year = int(year_elem.text)
                                pub_date = year_elem.text
                            except:
                                pass
                        else:
                            # Try MedlineDate for complex dates
                            medline_date = pub_date_elem.find('.//MedlineDate')
                            if medline_date is not None and medline_date.text:
                                try:
                                    # Extract year from formats like "2023 Jan-Feb" or "2023"
                                    year_match = medline_date.text.split()[0]
                                    year = int(year_match)
                                    pub_date = year_match
                                except:
                                    pass
                    
                    # Journal/Venue
                    venue = "Unknown Journal"
                    journal_elem = article_elem.find('.//Journal')
                    if journal_elem is not None:
                        title_elem = journal_elem.find('.//Title')
                        if title_elem is not None:
                            venue = title_elem.text
                        else:
                            # Try ISOAbbreviation as fallback
                            iso_elem = journal_elem.find('.//ISOAbbreviation')
                            if iso_elem is not None:
                                venue = iso_elem.text
                    
                    papers.append({
                        'id': f"pmid:{pmid}",
                        'title': title,
                        'authors': authors,
                        'year': year,
                        'citation_count': 0,  # PubMed doesn't provide citation counts directly
                        'abstract': abstract,
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'venue': venue,
                        'publication_date': pub_date,
                        'reference_count': 0,
                        'influential_citation_count': 0,
                        'source': 'PubMed'
                    })
                    
                except Exception as e:
                    print(f"Warning: Skipping malformed PubMed entry: {e}")
                    continue
            
            print(f"✅ Found {len(papers)} papers from PubMed")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching PubMed: {e}")
            return []
    
    def _search_crossref(self, query: str, limit: int) -> List[Dict]:
        """Search CrossRef API for DOI-indexed papers"""
        try:
            url = f"{self.config.CROSSREF_API_BASE}"
            params = {
                'query': query,
                'rows': limit,
                'sort': 'relevance',
                'order': 'desc'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for item in data.get('message', {}).get('items', []):
                try:
                    # Extract title
                    title = item.get('title', ['Unknown Title'])[0] if item.get('title') else 'Unknown Title'
                    
                    # Extract authors
                    authors = []
                    for author in item.get('author', []):
                        given = author.get('given', '')
                        family = author.get('family', '')
                        if family:
                            name = f"{given} {family}".strip()
                            authors.append(name)
                    
                    # Extract year
                    year = None
                    pub_date = item.get('published-print') or item.get('published-online')
                    if pub_date and 'date-parts' in pub_date:
                        try:
                            year = pub_date['date-parts'][0][0]
                        except:
                            pass
                    
                    # Extract venue
                    venue = item.get('container-title', ['Unknown'])[0] if item.get('container-title') else 'Unknown'
                    
                    # DOI and URL
                    doi = item.get('DOI', '')
                    url = f"https://doi.org/{doi}" if doi else item.get('URL', '')
                    
                    # Abstract (not always available in CrossRef)
                    abstract = item.get('abstract', '')
                    
                    papers.append({
                        'id': f"doi:{doi}" if doi else f"crossref:{item.get('URL', 'unknown')}",
                        'title': title,
                        'authors': authors,
                        'year': year,
                        'citation_count': item.get('is-referenced-by-count', 0),
                        'abstract': abstract,
                        'url': url,
                        'venue': venue,
                        'publication_date': str(year) if year else None,
                        'reference_count': item.get('references-count', 0),
                        'influential_citation_count': 0,
                        'source': 'CrossRef'
                    })
                    
                except Exception as e:
                    continue  # Skip malformed entries
            
            print(f"✅ Found {len(papers)} papers from CrossRef")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching CrossRef: {e}")
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
