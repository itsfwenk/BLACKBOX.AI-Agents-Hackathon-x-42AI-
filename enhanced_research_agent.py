#!/usr/bin/env python3
"""
Enhanced Research AI Agent - Configurable paper limits
Enhanced with multi-source search: Semantic Scholar, PubMed, arXiv, CrossRef
"""
import requests
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
from typing import List, Dict, Optional

class EnhancedConfig:
    # API Endpoints
    SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
    ARXIV_API_BASE = "http://export.arxiv.org/api/query"
    CROSSREF_API_BASE = "https://api.crossref.org/works"
    PUBMED_API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # Search Parameters - Now configurable!
    DEFAULT_MAX_PAPERS = 100  # Increased default
    API_DELAY_SECONDS = 1

class EnhancedPaperSearcher:
    def __init__(self):
        self.config = EnhancedConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-AI-Agent/1.0'
        })
    
    def search_papers(self, query: str, max_results: int = None, per_source_limit: int = None) -> Dict:
        """
        Search for papers using multiple sources
        
        Args:
            query: Search query
            max_results: Total maximum papers to return (default: 100)
            per_source_limit: Maximum papers per source (default: max_results/4)
        """
        if max_results is None:
            max_results = self.config.DEFAULT_MAX_PAPERS
        
        if per_source_limit is None:
            per_source_limit = max(max_results // 4, 10)
        
        print(f"🔍 Searching for papers on: '{query}'")
        print(f"📊 Target: {max_results} total papers ({per_source_limit} per source)")
        print("=" * 60)
        
        # Search all sources
        semantic_papers = self._search_semantic_scholar(query, per_source_limit)
        pubmed_papers = self._search_pubmed(query, per_source_limit)
        arxiv_papers = self._search_arxiv(query, per_source_limit)
        crossref_papers = self._search_crossref(query, per_source_limit)
        
        # Combine and deduplicate
        all_papers = self._combine_and_deduplicate(
            semantic_papers, pubmed_papers, arxiv_papers, crossref_papers
        )
        
        # Limit to max_results if specified
        if len(all_papers) > max_results:
            # Sort by citation count first, then by year
            all_papers.sort(key=lambda x: (x['citation_count'], x['year'] or 0), reverse=True)
            all_papers = all_papers[:max_results]
        
        return {
            'query': query,
            'total_papers': len(all_papers),
            'papers': all_papers,
            'sources_used': ['Semantic Scholar', 'PubMed', 'arXiv', 'CrossRef'],
            'search_timestamp': datetime.now().isoformat(),
            'search_params': {
                'max_results': max_results,
                'per_source_limit': per_source_limit
            }
        }
    
    def _search_semantic_scholar(self, query: str, limit: int) -> List[Dict]:
        """Search Semantic Scholar API"""
        try:
            # Semantic Scholar has a max limit of 100 per request
            actual_limit = min(limit, 100)
            
            url = f"{self.config.SEMANTIC_SCHOLAR_API_BASE}/paper/search"
            params = {
                'query': query,
                'limit': actual_limit,
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
            
            print(f"✅ Found {len(papers)} papers from Semantic Scholar (requested: {actual_limit})")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching Semantic Scholar: {e}")
            return []
    
    def _search_pubmed(self, query: str, limit: int) -> List[Dict]:
        """Search PubMed API"""
        try:
            # PubMed allows up to 10,000 results but we'll be reasonable
            actual_limit = min(limit, 200)
            
            # Step 1: Search for PMIDs
            search_url = f"{self.config.PUBMED_API_BASE}/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': actual_limit,
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
            
            # Step 2: Fetch detailed information in batches (PubMed recommends max 200 at a time)
            papers = []
            batch_size = 50
            
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i + batch_size]
                
                fetch_url = f"{self.config.PUBMED_API_BASE}/efetch.fcgi"
                fetch_params = {
                    'db': 'pubmed',
                    'id': ','.join(batch_pmids),
                    'retmode': 'xml'
                }
                
                fetch_response = self.session.get(fetch_url, params=fetch_params)
                fetch_response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(fetch_response.content)
                
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
                
                time.sleep(self.config.API_DELAY_SECONDS)
            
            print(f"✅ Found {len(papers)} papers from PubMed (requested: {actual_limit})")
            return papers
            
        except Exception as e:
            print(f"❌ Error searching PubMed: {e}")
            return []
    
    def _search_arxiv(self, query: str, limit: int) -> List[Dict]:
        """Search arXiv API"""
        try:
            # arXiv allows up to 30,000 results but we'll be reasonable
            actual_limit = min(limit, 100)
            
            formatted_query = quote(f'all:{query}')
            url = f"{self.config.ARXIV_API_BASE}?search_query={formatted_query}&start=0&max_results={actual_limit}"
            
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
            
            print(f"✅ Found {len(papers)} papers from arXiv (requested: {actual_limit})")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching arXiv: {e}")
            return []
    
    def _search_crossref(self, query: str, limit: int) -> List[Dict]:
        """Search CrossRef API"""
        try:
            # CrossRef allows up to 1000 results per request
            actual_limit = min(limit, 100)
            
            url = f"{self.config.CROSSREF_API_BASE}"
            params = {
                'query': query,
                'rows': actual_limit,
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
            
            print(f"✅ Found {len(papers)} papers from CrossRef (requested: {actual_limit})")
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

class EnhancedResearchAgent:
    def __init__(self):
        self.searcher = EnhancedPaperSearcher()
    
    def research_topic(self, query: str, max_papers: int = 100) -> str:
        """Research a topic and generate a report"""
        print(f"🤖 Enhanced Research Agent analyzing: '{query}'")
        print(f"🎯 Target: {max_papers} papers")
        print("=" * 60)
        
        # Search for papers
        results = self.searcher.search_papers(query, max_results=max_papers)
        
        if results['total_papers'] == 0:
            return "No papers found for the given query."
        
        # Generate report
        report = self._generate_enhanced_report(results)
        return report
    
    def _generate_enhanced_report(self, results: Dict) -> str:
        """Generate an enhanced report"""
        papers = results['papers']
        
        # Sort by citation count and year
        most_cited = sorted([p for p in papers if p['citation_count'] > 0], 
                           key=lambda x: x['citation_count'], reverse=True)[:10]
        
        recent_papers = sorted([p for p in papers if p['year'] and p['year'] >= 2020], 
                              key=lambda x: x['year'] or 0, reverse=True)[:10]
        
        # Count by source
        sources = {}
        for paper in papers:
            source = paper['source']
            sources[source] = sources.get(source, 0) + 1
        
        # Year distribution
        year_counts = {}
        for paper in papers:
            year = paper.get('year')
            if year:
                year_counts[year] = year_counts.get(year, 0) + 1
        
        report = f"""
# Enhanced Research Report: {results['query']}

## Summary
- **Total papers analyzed**: {results['total_papers']:,}
- **Sources searched**: {', '.join(results['sources_used'])}
- **Search completed**: {results['search_timestamp'][:19]}
- **Search parameters**: Max {results['search_params']['max_results']} papers, {results['search_params']['per_source_limit']} per source

## Papers by Source:
"""
        for source, count in sources.items():
            report += f"- **{source}**: {count} papers\n"
        
        # Year distribution
        if year_counts:
            sorted_years = sorted(year_counts.items(), reverse=True)
            report += f"\n## Publication Years:\n"
            for year, count in sorted_years[:10]:
                report += f"- **{year}**: {count} papers\n"
        
        report += "\n## Most Cited Papers:\n"
        for i, paper in enumerate(most_cited, 1):
            authors_str = ", ".join(paper['authors'][:3])
            if len(paper['authors']) > 3:
                authors_str += " et al."
            
            report += f"""
### {i}. {paper['title']}
- **Authors**: {authors_str}
- **Year**: {paper.get('year', 'N/A')} | **Citations**: {paper['citation_count']:,} | **Source**: {paper['source']}
- **Venue**: {paper.get('venue', 'N/A')}
- **URL**: {paper.get('url', 'N/A')}
"""
        
        report += "\n## Recent Papers (2020+):\n"
        for i, paper in enumerate(recent_papers, 1):
            authors_str = ", ".join(paper['authors'][:2])
            if len(paper['authors']) > 2:
                authors_str += " et al."
            
            report += f"""
### {i}. {paper['title']}
- **Authors**: {authors_str}
- **Year**: {paper.get('year', 'N/A')} | **Source**: {paper['source']}
- **Venue**: {paper.get('venue', 'N/A')}
- **URL**: {paper.get('url', 'N/A')}
"""
        
        return report

def main():
    """Main function for enhanced usage"""
    print("🚀 Enhanced Research AI Agent")
    print("Searches: Semantic Scholar, PubMed, arXiv, CrossRef")
    print("✨ Configurable paper limits!")
    print("=" * 60)
    
    agent = EnhancedResearchAgent()
    
    while True:
        try:
            query = input("\n📝 Enter your research query (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                print("Please enter a valid query.")
                continue
            
            # Ask for number of papers
            while True:
                try:
                    max_papers_input = input("📊 How many papers do you want? (default: 100, max recommended: 500): ").strip()
                    if not max_papers_input:
                        max_papers = 100
                        break
                    max_papers = int(max_papers_input)
                    if max_papers <= 0:
                        print("Please enter a positive number.")
                        continue
                    if max_papers > 1000:
                        print("⚠️  Warning: Very large requests may take a long time and hit API limits.")
                        confirm = input("Continue? (y/n): ").strip().lower()
                        if confirm not in ['y', 'yes']:
                            continue
                    break
                except ValueError:
                    print("Please enter a valid number.")
            
            # Generate research report
            report = agent.research_topic(query, max_papers)
            print("\n" + "="*60)
            print("📊 ENHANCED RESEARCH REPORT")
            print("="*60)
            print(report)
            
            # Ask if user wants to save
            save = input("\n💾 Save report to file? (y/n): ").strip().lower()
            if save in ['y', 'yes']:
                filename = f"enhanced_report_{query.replace(' ', '_')[:30]}_{max_papers}papers.txt"
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
