#!/usr/bin/env python3
"""
Simplified Research AI Agent using only standard library
"""
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import re

class SimpleResearchAgent:
    def __init__(self):
        self.api_delay = 2  # Longer delay to avoid rate limiting
    
    def research_topic(self, query):
        """Research a topic using available APIs"""
        print(f"🤖 Research Agent analyzing: '{query}'")
        print("=" * 60)
        
        # Search arXiv (more reliable for our test)
        arxiv_papers = self._search_arxiv(query)
        
        # Try Semantic Scholar with delay
        time.sleep(self.api_delay)
        semantic_papers = self._search_semantic_scholar(query)
        
        # Combine results
        all_papers = arxiv_papers + semantic_papers
        
        if not all_papers:
            return "❌ No papers found. Try a different query or check internet connection."
        
        # Generate report
        report = self._generate_report(query, all_papers)
        return report
    
    def _search_arxiv(self, query, max_results=10):
        """Search arXiv API"""
        print(f"🔍 Searching arXiv for '{query}'...")
        
        try:
            encoded_query = urllib.parse.quote(f'all:{query}')
            url = f"http://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=relevance"
            
            with urllib.request.urlopen(url) as response:
                xml_data = response.read().decode()
            
            # Parse XML
            root = ET.fromstring(xml_data)
            papers = []
            
            # Define namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                published_elem = entry.find('atom:published', ns)
                authors = entry.findall('atom:author', ns)
                id_elem = entry.find('atom:id', ns)
                
                # Extract data
                title = title_elem.text.strip() if title_elem is not None else 'Unknown Title'
                abstract = summary_elem.text.strip() if summary_elem is not None else ''
                
                # Parse publication date
                year = None
                if published_elem is not None:
                    try:
                        year = int(published_elem.text[:4])
                    except:
                        pass
                
                # Extract arXiv ID
                arxiv_id = 'unknown'
                if id_elem is not None:
                    arxiv_id = id_elem.text.split('/')[-1]
                
                # Extract authors
                author_names = []
                for author in authors:
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None:
                        author_names.append(name_elem.text)
                
                papers.append({
                    'title': title,
                    'authors': author_names,
                    'year': year,
                    'abstract': abstract[:300] + "..." if len(abstract) > 300 else abstract,
                    'source': 'arXiv',
                    'url': f"https://arxiv.org/abs/{arxiv_id}",
                    'citation_count': 0  # arXiv doesn't provide citation counts
                })
            
            print(f"✅ Found {len(papers)} papers from arXiv")
            return papers
            
        except Exception as e:
            print(f"❌ Error searching arXiv: {e}")
            return []
    
    def _search_semantic_scholar(self, query, max_results=10):
        """Search Semantic Scholar API with rate limiting protection"""
        print(f"🔍 Searching Semantic Scholar for '{query}'...")
        
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={max_results}&fields=paperId,title,authors,year,citationCount,abstract,url"
            
            # Add user agent to be polite
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Research-AI-Agent/1.0 (educational-use)')
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
            
            papers = []
            for paper in data.get('data', []):
                authors = [author.get('name', 'Unknown') for author in paper.get('authors', [])]
                
                papers.append({
                    'title': paper.get('title', 'Unknown Title'),
                    'authors': authors,
                    'year': paper.get('year'),
                    'abstract': (paper.get('abstract', '')[:300] + "...") if paper.get('abstract') and len(paper.get('abstract', '')) > 300 else paper.get('abstract', ''),
                    'source': 'Semantic Scholar',
                    'url': paper.get('url', ''),
                    'citation_count': paper.get('citationCount', 0)
                })
            
            print(f"✅ Found {len(papers)} papers from Semantic Scholar")
            return papers
            
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("⚠️ Semantic Scholar rate limit reached - using arXiv results only")
            else:
                print(f"❌ Error searching Semantic Scholar: HTTP {e.code}")
            return []
        except Exception as e:
            print(f"❌ Error searching Semantic Scholar: {e}")
            return []
    
    def _generate_report(self, query, papers):
        """Generate a simple research report"""
        # Sort papers by citation count (Semantic Scholar) and year (arXiv)
        semantic_papers = [p for p in papers if p['source'] == 'Semantic Scholar']
        arxiv_papers = [p for p in papers if p['source'] == 'arXiv']
        
        # Sort by citations for Semantic Scholar papers
        most_cited = sorted(semantic_papers, key=lambda x: x['citation_count'], reverse=True)
        
        # Sort by year for arXiv papers (most recent first)
        recent_papers = sorted(arxiv_papers, key=lambda x: x['year'] or 0, reverse=True)
        
        report = f"""
# Research Report: {query}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total papers analyzed: {len(papers)}

## Summary
- Semantic Scholar papers: {len(semantic_papers)}
- arXiv papers: {len(arxiv_papers)}

"""
        
        if most_cited:
            report += """
## Most Cited Papers (Semantic Scholar)

"""
            for i, paper in enumerate(most_cited[:5], 1):
                authors_str = ", ".join(paper['authors'][:3])
                if len(paper['authors']) > 3:
                    authors_str += " et al."
                
                report += f"""
### {i}. {paper['title']}
- Authors: {authors_str}
- Year: {paper.get('year', 'Unknown')}
- Citations: {paper['citation_count']:,}
- Source: {paper['source']}
- URL: {paper.get('url', 'N/A')}

Abstract: {paper['abstract']}

"""
        
        if recent_papers:
            report += """
## Recent Papers (arXiv)

"""
            for i, paper in enumerate(recent_papers[:5], 1):
                authors_str = ", ".join(paper['authors'][:3])
                if len(paper['authors']) > 3:
                    authors_str += " et al."
                
                report += f"""
### {i}. {paper['title']}
- Authors: {authors_str}
- Year: {paper.get('year', 'Unknown')}
- Source: {paper['source']}
- URL: {paper.get('url', 'N/A')}

Abstract: {paper['abstract']}

"""
        
        # Simple analysis
        all_years = [p['year'] for p in papers if p['year']]
        if all_years:
            year_range = f"{min(all_years)} - {max(all_years)}"
            avg_year = sum(all_years) / len(all_years)
        else:
            year_range = "Unknown"
            avg_year = 0
        
        total_citations = sum(p['citation_count'] for p in papers)
        
        report += f"""
## Analysis Summary

- Publication year range: {year_range}
- Average publication year: {avg_year:.1f}
- Total citations: {total_citations:,}
- Average citations per paper: {total_citations / len(papers) if papers else 0:.1f}

## Research Insights

Based on the analyzed papers:
"""
        
        if len(recent_papers) > len(most_cited):
            report += "- This appears to be an active, rapidly evolving research area with many recent publications\n"
        elif total_citations > 1000:
            report += "- This is a well-established research area with significant citation impact\n"
        else:
            report += "- This appears to be an emerging or niche research area\n"
        
        if semantic_papers and arxiv_papers:
            report += "- Research spans both peer-reviewed publications and preprints, indicating active development\n"
        
        report += f"""
---
*Report generated by Simple Research AI Agent*
"""
        
        return report

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        print("""
🤖 Simple Research AI Agent

Usage: python3 simple_agent.py "your research query"

Examples:
  python3 simple_agent.py "machine learning"
  python3 simple_agent.py "quantum computing"
  python3 simple_agent.py "CRISPR gene editing"
        """)
        return
    
    query = " ".join(sys.argv[1:])
    
    agent = SimpleResearchAgent()
    report = agent.research_topic(query)
    
    print("\n" + "="*80)
    print(report)

if __name__ == "__main__":
    main()
