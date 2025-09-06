#!/usr/bin/env python3
"""
Standalone Research AI Agent - No external dependencies required
Enhanced with multi-source search: Semantic Scholar, PubMed, arXiv, CrossRef
"""
import requests
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
from typing import List, Dict, Optional

class SimpleConfig:
    # API Endpoints
    SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
    ARXIV_API_BASE = "http://export.arxiv.org/api/query"
    CROSSREF_API_BASE = "https://api.crossref.org/works"
    PUBMED_API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # Search Parameters
    MAX_PAPERS_PER_QUERY = 40
    API_DELAY_SECONDS = 1

class SimplePaperSearcher:
    def __init__(self):
        self.config = SimpleConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-AI-Agent/1.0'
        })
    
    def search_papers(self, query: str, max_results: int = None) -> Dict:
        """Search for papers using multiple sources"""
        if max_results is None:
            max_results = self.config.MAX_PAPERS_PER_QUERY
        
        print(f"🔍 Searching for papers on: '{query}'")
        print("=" * 60)
        
        per_source_limit = max(max_results // 4, 10)
        
        # Search all sources
        semantic_papers = self._search_semantic_scholar(query, per_source_limit)
        pubmed_papers = self._search_pubmed(query, per_source_limit)
        arxiv_papers = self._search_arxiv(query, per_source_limit)
        crossref_papers = self._search_crossref(query, per_source_limit)
        
        # Combine and deduplicate
        all_papers = self._combine_and_deduplicate(
            semantic_papers, pubmed_papers, arxiv_papers, crossref_papers
        )
        
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
                    'abstract': paper.get('abstract', ''),
                    'source': 'Semantic Scholar',
                    'url': paper.get('url', ''),
                    'venue': paper.get('venue', '')
                })
            
            print(f"✅ Found {len(papers)} papers from Semantic Scholar")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching Semantic Scholar: {e}")
            return []
    
    def _search_pubmed(self, query: str, limit: int) -> List[Dict]:
        """Search PubMed API"""
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
            
            # Step 2: Fetch detailed information
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
                    medline_citation = article.find('.//MedlineCitation')
                    if medline_citation is None:
                        continue
                        
                    pmid_elem = medline_citation.find('.//PMID')
                    pmid = pmid_elem.text if pmid_elem is not None else 'unknown'
                    
                    article_elem = medline_citation.find('.//Article')
                    if article_elem is None:
                        continue
                    
                    # Title
                    title_elem = article_elem.find('.//ArticleTitle')
                    title = ""
                    if title_elem is not None:
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
                            
                            if last_name_elem is not None:
                                name = last_name_elem.text
                                if first_name_elem is not None:
                                    name = f"{first_name_elem.text} {name}"
                                authors.append(name)
                    
                    # Abstract
                    abstract = ""
                    abstract_elem = article_elem.find('.//Abstract')
                    if abstract_elem is not None:
                        abstract_texts = []
                        for abs_text in abstract_elem.findall('.//AbstractText'):
                            if abs_text.text:
                                abstract_texts.append(abs_text.text.strip())
                        abstract = " ".join(abstract_texts)
                    
                    # Year
                    year = None
                    pub_date_elem = article_elem.find('.//PubDate')
                    if pub_date_elem is not None:
                        year_elem = pub_date_elem.find('.//Year')
                        if year_elem is not None:
                            try:
                                year = int(year_elem.text)
                            except:
                                pass
                    
                    # Venue
                    venue = "Unknown Journal"
                    journal_elem = article_elem.find('.//Journal')
                    if journal_elem is not None:
                        title_elem = journal_elem.find('.//Title')
                        if title_elem is not None:
                            venue = title_elem.text
                    
                    papers.append({
                        'title': title,
                        'authors': authors,
                        'year': year,
                        'citation_count': 0,
                        'abstract': abstract,
                        'source': 'PubMed',
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'venue': venue
                    })
                    
                except Exception:
                    continue
            
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
                summary = entry.find('atom:summary', ns)
                published = entry.find('atom:published', ns)
                authors = entry.findall('atom:author', ns)
                id_elem = entry.find('atom:id', ns)
                
                arxiv_id = id_elem.text.split('/')[-1] if id_elem is not None else 'unknown'
                
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
                    'abstract': summary.text.strip() if summary is not None else '',
                    'source': 'arXiv',
                    'url': f"https://arxiv.org/abs/{arxiv_id}",
                    'venue': 'arXiv'
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
                    'abstract': '',
                    'source': 'CrossRef',
                    'url': f"https://doi.org/{item.get('DOI', '')}" if item.get('DOI') else '',
                    'venue': item.get('container-title', ['Unknown'])[0] if item.get('container-title') else 'Unknown'
                })
            
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
                if title_normalized not in seen_titles and len(title_normalized) > 10:
                    seen_titles.add(title_normalized)
                    all_papers.append(paper)
        
        return all_papers

class SimpleResearchAgent:
    def __init__(self):
        self.searcher = SimplePaperSearcher()
    
    def research_topic(self, query: str) -> str:
        """Research a topic and generate a simple report"""
        print(f"🤖 Research Agent analyzing: '{query}'")
        print("=" * 60)
        
        # Search for papers
        results = self.searcher.search_papers(query)
        
        if results['total_papers'] == 0:
            return "No papers found for the given query."
        
        # Generate simple report
        report = self._generate_simple_report(results)
        return report
    
    def _generate_simple_report(self, results: Dict) -> str:
        """Generate a simple text report"""
        papers = results['papers']
        
        # Sort by citation count and year
        most_cited = sorted([p for p in papers if p['citation_count'] > 0], 
                           key=lambda x: x['citation_count'], reverse=True)[:5]
        
        recent_papers = sorted([p for p in papers if p['year'] and p['year'] >= 2020], 
                              key=lambda x: x['year'] or 0, reverse=True)[:5]
        
        # Count by source
        sources = {}
        for paper in papers:
            source = paper['source']
            sources[source] = sources.get(source, 0) + 1
        
        report = f"""
# Research Report: {results['query']}

## Summary
- Total papers analyzed: {results['total_papers']}
- Sources searched: {', '.join(results['sources_used'])}
- Search completed: {results['search_timestamp'][:19]}

## Papers by Source:
"""
        for source, count in sources.items():
            report += f"- {source}: {count} papers\n"
        
        report += "\n## Most Cited Papers:\n"
        for i, paper in enumerate(most_cited, 1):
            authors_str = ", ".join(paper['authors'][:3])
            if len(paper['authors']) > 3:
                authors_str += " et al."
            
            report += f"""
{i}. {paper['title']}
   Authors: {authors_str}
   Year: {paper.get('year', 'N/A')} | Citations: {paper['citation_count']} | Source: {paper['source']}
   URL: {paper.get('url', 'N/A')}
"""
        
        report += "\n## Recent Papers (2020+):\n"
        for i, paper in enumerate(recent_papers, 1):
            authors_str = ", ".join(paper['authors'][:2])
            if len(paper['authors']) > 2:
                authors_str += " et al."
            
            report += f"""
{i}. {paper['title']}
   Authors: {authors_str}
   Year: {paper.get('year', 'N/A')} | Source: {paper['source']}
   URL: {paper.get('url', 'N/A')}
"""
        
        return report

def main():
    """Main function for standalone usage"""
    print("🤖 Enhanced Research AI Agent")
    print("Searches: Semantic Scholar, PubMed, arXiv, CrossRef")
    print("=" * 60)
    
    agent = SimpleResearchAgent()
    
    while True:
        try:
            query = input("\n📝 Enter your research query (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                print("Please enter a valid query.")
                continue
            
            # Generate research report
            report = agent.research_topic(query)
            print("\n" + "="*60)
            print("📊 RESEARCH REPORT")
            print("="*60)
            print(report)
            
            # Ask if user wants to save
            save = input("\n💾 Save report to file? (y/n): ").strip().lower()
            if save in ['y', 'yes']:
                filename = f"research_report_{query.replace(' ', '_')[:30]}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"✅ Report saved to {filename}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
