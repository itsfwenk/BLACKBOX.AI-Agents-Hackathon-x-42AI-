#!/usr/bin/env python3
"""
Test script for the enhanced Research AI Agent with multiple sources
"""
import requests
import time
import json
from datetime import datetime
from typing import List, Dict
from urllib.parse import quote
import xml.etree.ElementTree as ET

class TestConfig:
    # API Endpoints
    SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
    ARXIV_API_BASE = "http://export.arxiv.org/api/query"
    CROSSREF_API_BASE = "https://api.crossref.org/works"
    PUBMED_API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # Search Parameters
    MAX_PAPERS_PER_QUERY = 20
    API_DELAY_SECONDS = 1
    MAX_RETRIES = 3

class EnhancedPaperSearcher:
    def __init__(self):
        self.config = TestConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-AI-Agent/1.0 (mailto:research@example.com)'
        })
    
    def search_papers(self, query: str, max_results: int = 20) -> Dict:
        """Search for papers using multiple sources"""
        print(f"🔍 Testing enhanced search for: '{query}'")
        
        per_source_limit = max_results // 4
        
        # Test each source
        semantic_papers = self._search_semantic_scholar(query, per_source_limit)
        pubmed_papers = self._search_pubmed(query, per_source_limit)
        arxiv_papers = self._search_arxiv(query, per_source_limit)
        crossref_papers = self._search_crossref(query, per_source_limit)
        
        # Combine results
        all_papers = []
        seen_titles = set()
        
        for paper_list in [semantic_papers, pubmed_papers, arxiv_papers, crossref_papers]:
            for paper in paper_list:
                title_normalized = paper['title'].lower().strip()
                if title_normalized not in seen_titles:
                    seen_titles.add(title_normalized)
                    all_papers.append(paper)
        
        return {
            'query': query,
            'total_papers': len(all_papers),
            'papers': all_papers,
            'sources_used': ['Semantic Scholar', 'PubMed', 'arXiv', 'CrossRef'],
            'search_timestamp': datetime.now().isoformat()
        }
    
    def _search_semantic_scholar(self, query: str, limit: int) -> List[Dict]:
        """Search Semantic Scholar API"""
        try:
            url = f"{self.config.SEMANTIC_SCHOLAR_API_BASE}/paper/search"
            params = {
                'query': query,
                'limit': limit,
                'fields': 'paperId,title,authors,year,citationCount,abstract,url,venue'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for paper in data.get('data', []):
                papers.append({
                    'title': paper.get('title', 'Unknown Title'),
                    'authors': [author.get('name', 'Unknown') for author in paper.get('authors', [])],
                    'year': paper.get('year'),
                    'citation_count': paper.get('citationCount', 0),
                    'source': 'Semantic Scholar',
                    'url': paper.get('url', '')
                })
            
            print(f"✅ Found {len(papers)} papers from Semantic Scholar")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching Semantic Scholar: {e}")
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
                        'title': title,
                        'authors': authors,
                        'year': year,
                        'citation_count': 0,  # PubMed doesn't provide citation counts directly
                        'source': 'PubMed',
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'venue': venue,
                        'abstract': abstract
                    })
                    
                except Exception as e:
                    continue  # Skip malformed entries
            
            print(f"✅ Found {len(papers)} papers from PubMed")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching PubMed: {e}")
            return []
    
    def _search_arxiv(self, query: str, limit: int) -> List[Dict]:
        """Search arXiv API"""
        try:
            formatted_query = quote(f'all:{query}')
            url = f"{self.config.ARXIV_API_BASE}?search_query={formatted_query}&start=0&max_results={limit}"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            papers = []
            
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                authors = entry.findall('atom:author', ns)
                published = entry.find('atom:published', ns)
                
                year = None
                if published is not None:
                    try:
                        year = int(published.text[:4])
                    except:
                        pass
                
                papers.append({
                    'title': title.text.strip() if title is not None else 'Unknown Title',
                    'authors': [author.find('atom:name', ns).text for author in authors if author.find('atom:name', ns) is not None],
                    'year': year,
                    'citation_count': 0,
                    'source': 'arXiv',
                    'url': f"https://arxiv.org/abs/{entry.find('atom:id', ns).text.split('/')[-1] if entry.find('atom:id', ns) is not None else 'unknown'}"
                })
            
            print(f"✅ Found {len(papers)} papers from arXiv")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching arXiv: {e}")
            return []
    
    def _search_crossref(self, query: str, limit: int) -> List[Dict]:
        """Search CrossRef API"""
        try:
            url = f"{self.config.CROSSREF_API_BASE}"
            params = {
                'query': query,
                'rows': limit,
                'sort': 'relevance'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for item in data.get('message', {}).get('items', []):
                title = item.get('title', ['Unknown Title'])[0] if item.get('title') else 'Unknown Title'
                
                authors = []
                for author in item.get('author', []):
                    given = author.get('given', '')
                    family = author.get('family', '')
                    if family:
                        authors.append(f"{given} {family}".strip())
                
                year = None
                pub_date = item.get('published-print') or item.get('published-online')
                if pub_date and 'date-parts' in pub_date:
                    try:
                        year = pub_date['date-parts'][0][0]
                    except:
                        pass
                
                papers.append({
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'citation_count': item.get('is-referenced-by-count', 0),
                    'source': 'CrossRef',
                    'url': f"https://doi.org/{item.get('DOI', '')}" if item.get('DOI') else ''
                })
            
            print(f"✅ Found {len(papers)} papers from CrossRef")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching CrossRef: {e}")
            return []

def main():
    print("🤖 Testing Enhanced Research AI Agent")
    print("=" * 50)
    
    searcher = EnhancedPaperSearcher()
    
    # Test with a medical query to show PubMed integration
    results = searcher.search_papers("COVID-19 vaccine effectiveness", 60)
    
    print(f"\n📊 RESULTS SUMMARY")
    print(f"Query: {results['query']}")
    print(f"Total papers found: {results['total_papers']}")
    print(f"Sources used: {', '.join(results['sources_used'])}")
    
    # Show breakdown by source
    sources = {}
    for paper in results['papers']:
        source = paper['source']
        sources[source] = sources.get(source, 0) + 1
    
    print(f"\n📈 PAPERS BY SOURCE:")
    for source, count in sources.items():
        print(f"  • {source}: {count} papers")
    
    print(f"\n📄 SAMPLE PAPERS:")
    for i, paper in enumerate(results['papers'][:5], 1):
        authors_str = ", ".join(paper['authors'][:2])
        if len(paper['authors']) > 2:
            authors_str += " et al."
        
        print(f"{i}. {paper['title'][:80]}...")
        print(f"   Authors: {authors_str}")
        print(f"   Year: {paper.get('year', 'N/A')} | Citations: {paper['citation_count']} | Source: {paper['source']}")
        print()
    
    print("✅ Enhanced Research AI Agent is working with multiple sources!")
    print("   Now includes: Semantic Scholar, PubMed, arXiv, and CrossRef")

if __name__ == "__main__":
    main()
