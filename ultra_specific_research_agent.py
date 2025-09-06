#!/usr/bin/env python3
"""
Ultra-Specific Research AI Agent - Prioritizes papers that match the COMPLETE query
Solves the problem of getting generic papers on sub-topics instead of specific combinations
"""
import requests
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
from typing import List, Dict, Optional, Set
import re

class UltraSpecificConfig:
    # API Endpoints
    SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
    ARXIV_API_BASE = "http://export.arxiv.org/api/query"
    CROSSREF_API_BASE = "https://api.crossref.org/works"
    PUBMED_API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # Ultra-specific search parameters
    DEFAULT_MAX_PAPERS = 30
    API_DELAY_SECONDS = 1
    
    # Specificity thresholds (much higher than generic search)
    MIN_SPECIFICITY_SCORE = 0.6  # Only include papers with 60%+ specificity
    HIGH_SPECIFICITY_THRESHOLD = 0.8  # 80%+ = ultra-specific
    
    # Scoring weights (specificity is most important)
    SPECIFICITY_WEIGHT = 0.7  # 70% of total score
    CITATION_WEIGHT = 0.2     # 20% of total score  
    JOURNAL_WEIGHT = 0.1      # Only 10% of total score

class UltraSpecificPaperSearcher:
    def __init__(self):
        self.config = UltraSpecificConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Ultra-Specific-Research-Agent/1.0'
        })
    
    def _extract_query_components(self, query: str) -> Dict:
        """Extract all components of the query for ultra-specific matching"""
        # Clean and normalize query
        query_clean = query.lower().strip()
        
        # Split by common conjunctions
        if ' and ' in query_clean:
            main_parts = [part.strip() for part in query_clean.split(' and ')]
        elif ' in ' in query_clean:
            main_parts = [part.strip() for part in query_clean.split(' in ')]
        elif ' for ' in query_clean:
            main_parts = [part.strip() for part in query_clean.split(' for ')]
        else:
            main_parts = [query_clean]
        
        # Extract individual terms (remove stop words)
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'and', 'or'}
        all_terms = []
        for part in main_parts:
            terms = re.findall(r'\b\w+\b', part)
            all_terms.extend([term for term in terms if term not in stop_words and len(term) > 2])
        
        # Create phrase combinations
        phrases = []
        phrases.append(query_clean)  # Full query
        phrases.extend(main_parts)   # Main parts
        
        # 2-word and 3-word phrases from the query
        words = query_clean.split()
        for i in range(len(words) - 1):
            if words[i] not in stop_words and words[i+1] not in stop_words:
                phrases.append(f"{words[i]} {words[i+1]}")
        
        for i in range(len(words) - 2):
            if all(word not in stop_words for word in words[i:i+3]):
                phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        return {
            'full_query': query_clean,
            'main_parts': main_parts,
            'all_terms': list(set(all_terms)),
            'phrases': list(set(phrases)),
            'original_query': query
        }
    
    def _calculate_specificity_score(self, paper: Dict, query_components: Dict) -> float:
        """Calculate how specifically the paper matches the complete query"""
        title = paper.get('title', '') or ''
        abstract = paper.get('abstract', '') or ''
        title = title.lower()
        abstract = abstract.lower()
        
        if not title.strip():
            return 0.0
        
        # Combine title and abstract with title weighted more heavily
        title_weight = 3.0
        abstract_weight = 1.0
        
        score = 0.0
        max_score = 0.0
        
        # 1. EXACT PHRASE MATCHING (highest priority)
        max_score += 10.0
        for phrase in query_components['phrases']:
            if len(phrase.split()) >= 2:  # Only multi-word phrases
                if phrase in title:
                    score += 10.0 * title_weight  # Massive bonus for title phrase match
                elif phrase in abstract:
                    score += 8.0 * abstract_weight  # High bonus for abstract phrase match
        
        # 2. MAIN PARTS COVERAGE (critical for specificity)
        main_parts = query_components['main_parts']
        if len(main_parts) > 1:  # Multi-part query (e.g., "orchid soft rot AND phage therapy")
            max_score += 15.0
            parts_in_title = sum(1 for part in main_parts if part in title)
            parts_in_abstract = sum(1 for part in main_parts if part in abstract)
            
            # ALL parts must be present for high specificity
            if parts_in_title == len(main_parts):
                score += 15.0 * title_weight  # Perfect match in title
            elif parts_in_title + parts_in_abstract >= len(main_parts):
                score += 12.0  # All parts covered between title and abstract
            else:
                # Partial coverage penalty
                coverage_ratio = (parts_in_title * 2 + parts_in_abstract) / (len(main_parts) * 2)
                score += coverage_ratio * 8.0
        
        # 3. TERM COVERAGE (all terms should be present)
        all_terms = query_components['all_terms']
        if all_terms:
            max_score += 8.0
            terms_in_title = sum(1 for term in all_terms if term in title)
            terms_in_abstract = sum(1 for term in all_terms if term in abstract)
            
            total_term_coverage = (terms_in_title * title_weight + terms_in_abstract * abstract_weight)
            max_term_coverage = len(all_terms) * title_weight
            
            if max_term_coverage > 0:
                score += (total_term_coverage / max_term_coverage) * 8.0
        
        # 4. PENALIZE OVERLY GENERIC PAPERS
        generic_indicators = [
            'review', 'overview', 'survey', 'introduction', 'perspective', 'current state',
            'recent advances', 'future directions', 'challenges', 'opportunities',
            'comprehensive', 'systematic review', 'meta-analysis'
        ]
        
        generic_penalty = 0.0
        for indicator in generic_indicators:
            if indicator in title:
                generic_penalty += 3.0  # Heavy penalty for generic titles
            elif indicator in abstract[:200]:  # Early in abstract
                generic_penalty += 1.0
        
        # 5. BONUS FOR SPECIFIC APPLICATIONS/ORGANISMS
        specific_indicators = query_components['all_terms']
        specificity_bonus = 0.0
        for term in specific_indicators:
            if term in title:
                specificity_bonus += 1.0
        
        # Calculate final score
        raw_score = max(0.0, score + specificity_bonus - generic_penalty)
        
        # Normalize to 0-1 range
        if max_score > 0:
            normalized_score = min(raw_score / max_score, 1.0)
        else:
            normalized_score = 0.0
        
        return normalized_score
    
    def _create_ultra_specific_queries(self, query: str) -> List[str]:
        """Create search queries optimized for specificity"""
        queries = []
        
        # 1. Exact phrase query (highest specificity)
        queries.append(f'"{query}"')
        
        # 2. All terms with AND (high specificity)
        terms = query.split()
        if len(terms) > 1:
            queries.append(' AND '.join(f'"{term}"' for term in terms))
        
        # 3. Main parts with AND
        if ' and ' in query.lower():
            parts = [part.strip() for part in query.split(' and ')]
            if len(parts) == 2:
                queries.append(f'"{parts[0]}" AND "{parts[1]}"')
        
        # 4. Key term combinations
        if len(terms) >= 3:
            # Try different combinations of key terms
            queries.append(f'"{terms[0]} {terms[1]}" AND "{terms[-1]}"')
            if len(terms) >= 4:
                queries.append(f'"{terms[0]}" AND "{terms[1]} {terms[2]}" AND "{terms[-1]}"')
        
        # 5. Original query as fallback
        queries.append(query)
        
        return queries
    
    def search_papers(self, query: str, max_results: int = None) -> Dict:
        """Search for ultra-specific papers"""
        if max_results is None:
            max_results = self.config.DEFAULT_MAX_PAPERS
        
        # Analyze query components
        query_components = self._extract_query_components(query)
        search_queries = self._create_ultra_specific_queries(query)
        
        print(f"🎯 Ultra-Specific Search for: '{query}'")
        print(f"📝 Main parts: {', '.join(query_components['main_parts'])}")
        print(f"🔑 Key terms: {', '.join(query_components['all_terms'])}")
        print(f"🔍 Using {len(search_queries)} ultra-specific search strategies")
        print(f"📊 Target: {max_results} highly specific papers")
        print("=" * 60)
        
        # Search with multiple ultra-specific strategies
        all_papers = []
        
        for i, search_query in enumerate(search_queries, 1):
            print(f"🔍 Strategy {i}: {search_query}")
            
            # Search each source
            semantic_papers = self._search_semantic_scholar(search_query, max_results)
            pubmed_papers = self._search_pubmed_specific(search_query, max_results)
            crossref_papers = self._search_crossref(search_query, max_results)
            
            # Combine results from this strategy
            strategy_papers = self._combine_and_deduplicate(
                semantic_papers, pubmed_papers, crossref_papers
            )
            
            all_papers.extend(strategy_papers)
            
            # Stop early if we have enough highly specific papers
            if len(all_papers) > max_results * 3:
                break
        
        # Remove duplicates
        all_papers = self._combine_and_deduplicate([all_papers])
        
        print(f"📋 Found {len(all_papers)} total papers before specificity filtering")
        
        # Calculate specificity scores and filter
        ultra_specific_papers = []
        for paper in all_papers:
            specificity_score = self._calculate_specificity_score(paper, query_components)
            
            # Only include papers above minimum specificity threshold
            if specificity_score >= self.config.MIN_SPECIFICITY_SCORE:
                paper['specificity_score'] = specificity_score
                paper['is_ultra_specific'] = specificity_score >= self.config.HIGH_SPECIFICITY_THRESHOLD
                
                # Calculate combined quality score (specificity is most important)
                citation_score = min(paper.get('citation_count', 0) / 50, 1.0)  # Normalize citations
                journal_score = 0.5  # Default journal score (we don't prioritize this)
                
                paper['quality_score'] = (
                    specificity_score * self.config.SPECIFICITY_WEIGHT +
                    citation_score * self.config.CITATION_WEIGHT +
                    journal_score * self.config.JOURNAL_WEIGHT
                ) * 100
                
                ultra_specific_papers.append(paper)
        
        print(f"✅ {len(ultra_specific_papers)} papers passed ultra-specificity filter (min score: {self.config.MIN_SPECIFICITY_SCORE})")
        
        # Sort by specificity first, then quality
        ultra_specific_papers.sort(key=lambda x: (x['specificity_score'], x['quality_score']), reverse=True)
        
        # Limit results
        if len(ultra_specific_papers) > max_results:
            ultra_specific_papers = ultra_specific_papers[:max_results]
        
        ultra_specific_count = sum(1 for p in ultra_specific_papers if p.get('is_ultra_specific', False))
        
        return {
            'query': query,
            'total_papers': len(ultra_specific_papers),
            'papers': ultra_specific_papers,
            'sources_used': ['Semantic Scholar', 'PubMed', 'CrossRef'],
            'search_timestamp': datetime.now().isoformat(),
            'specificity_analysis': {
                'query_components': query_components,
                'ultra_specific_papers': ultra_specific_count,
                'avg_specificity_score': sum(p['specificity_score'] for p in ultra_specific_papers) / len(ultra_specific_papers) if ultra_specific_papers else 0,
                'search_strategies_used': len(search_queries),
                'min_specificity_threshold': self.config.MIN_SPECIFICITY_SCORE
            }
        }
    
    def _search_semantic_scholar(self, query: str, limit: int) -> List[Dict]:
        """Search Semantic Scholar with ultra-specific query"""
        try:
            actual_limit = min(limit, 50)
            
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
            
            print(f"  ✅ Semantic Scholar: {len(papers)} papers")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"  ❌ Semantic Scholar error: {e}")
            return []
    
    def _search_pubmed_specific(self, query: str, limit: int) -> List[Dict]:
        """Search PubMed with ultra-specific query handling"""
        try:
            actual_limit = min(limit, 100)
            
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
                print(f"  ✅ PubMed: 0 papers")
                return []
            
            time.sleep(self.config.API_DELAY_SECONDS)
            
            # Fetch details
            papers = []
            fetch_url = f"{self.config.PUBMED_API_BASE}/efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids[:actual_limit]),
                'retmode': 'xml'
            }
            
            fetch_response = self.session.get(fetch_url, params=fetch_params)
            fetch_response.raise_for_status()
            
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
                    
                    # Venue (Journal)
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
            
            print(f"  ✅ PubMed: {len(papers)} papers")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"  ❌ PubMed error: {e}")
            return []
    
    def _search_crossref(self, query: str, limit: int) -> List[Dict]:
        """Search CrossRef API"""
        try:
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
                    'abstract': '',  # CrossRef doesn't provide abstracts
                    'source': 'CrossRef',
                    'url': f"https://doi.org/{item.get('DOI', '')}" if item.get('DOI') else '',
                    'venue': item.get('container-title', ['Unknown'])[0] if item.get('container-title') else 'Unknown'
                })
            
            print(f"  ✅ CrossRef: {len(papers)} papers")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"  ❌ CrossRef error: {e}")
            return []
    
    def _combine_and_deduplicate(self, *paper_lists) -> List[Dict]:
        """Combine paper lists and remove duplicates"""
        all_papers = []
        seen_titles = set()
        
        # Flatten nested lists
        flat_papers = []
        for paper_list in paper_lists:
            if isinstance(paper_list, list) and len(paper_list) > 0 and isinstance(paper_list[0], list):
                # Nested list
                for sublist in paper_list:
                    flat_papers.extend(sublist)
            else:
                flat_papers.extend(paper_list)
        
        for paper in flat_papers:
            title_normalized = paper['title'].lower().strip()
            if title_normalized not in seen_titles and len(title_normalized) > 10:
                seen_titles.add(title_normalized)
                all_papers.append(paper)
        
        return all_papers

class UltraSpecificResearchAgent:
    def __init__(self):
        self.searcher = UltraSpecificPaperSearcher()
    
    def research_topic(self, query: str, max_papers: int = 30) -> str:
        """Research a topic with ultra-specific focus"""
        print(f"🎯 Ultra-Specific Research Agent analyzing: '{query}'")
        print(f"🔍 Focus: Finding papers that match your COMPLETE query, not just sub-topics")
        print(f"📊 Target: {max_papers} ultra-specific papers")
        print("=" * 60)
        
        # Search for papers
        results = self.searcher.search_papers(query, max_results=max_papers)
        
        if results['total_papers'] == 0:
            return "No ultra-specific papers found for the given query. Try a broader search or check spelling."
        
        # Generate report
        report = self._generate_ultra_specific_report(results)
        return report
    
    def _generate_ultra_specific_report(self, results: Dict) -> str:
        """Generate an ultra-specific focused report"""
        papers = results['papers']
        specificity_analysis = results['specificity_analysis']
        
        # Separate papers by specificity
        ultra_specific = [p for p in papers if p.get('is_ultra_specific', False)]
        highly_specific = [p for p in papers if not p.get('is_ultra_specific', False)]
        
        report = f"""
# Ultra-Specific Research Report: {results['query']}

## 🎯 Specificity Summary
- **Total ultra-specific papers found**: {results['total_papers']:,}
- **Ultra-specific papers (≥80% match)**: {specificity_analysis['ultra_specific_papers']} ({specificity_analysis['ultra_specific_papers']/results['total_papers']*100:.1f}%)
- **Average specificity score**: {specificity_analysis['avg_specificity_score']:.2f}/1.0
- **Query components analyzed**: {len(specificity_analysis['query_components']['main_parts'])} main parts, {len(specificity_analysis['query_components']['all_terms'])} key terms
- **Search strategies used**: {specificity_analysis['search_strategies_used']}
- **Minimum specificity threshold**: {specificity_analysis['min_specificity_threshold']:.1f}

## 📊 Papers by Source:
"""
        sources = {}
        for paper in papers:
            source = paper['source']
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sources.items():
            report += f"- **{source}**: {count} papers\n"
        
        if ultra_specific:
            report += f"\n## 🎯 Ultra-Specific Papers (≥80% Query Match):\n"
            for i, paper in enumerate(ultra_specific, 1):
                authors_str = ", ".join(paper['authors'][:3])
                if len(paper['authors']) > 3:
                    authors_str += " et al."
                
                report += f"""
### {i}. {paper['title']}
- **Authors**: {authors_str}
- **Journal**: {paper.get('venue', 'N/A')}
- **Year**: {paper.get('year', 'N/A')} | **Citations**: {paper['citation_count']:,} | **Source**: {paper['source']}
- **Specificity Score**: {paper['specificity_score']:.2f}/1.0 🎯
- **Quality Score**: {paper.get('quality_score', 0):.1f}/100
- **URL**: {paper.get('url', 'N/A')}
"""
                if paper.get('abstract') and len(paper['abstract']) > 50:
                    abstract = paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract']
                    report += f"- **Abstract**: {abstract}\n"
        
        report += f"\n## 📈 All Ultra-Specific Papers (Ranked by Specificity):\n"
        for i, paper in enumerate(papers, 1):
            authors_str = ", ".join(paper['authors'][:2])
            if len(paper['authors']) > 2:
                authors_str += " et al."
            
            specificity_indicator = " 🎯" if paper.get('is_ultra_specific', False) else ""
            
            report += f"""
### {i}. {paper['title']}
- **Authors**: {authors_str}
- **Journal**: {paper.get('venue', 'N/A')}
- **Year**: {paper.get('year', 'N/A')} | **Citations**: {paper['citation_count']:,} | **Source**: {paper['source']}
- **Specificity Score**: {paper['specificity_score']:.2f}/1.0{specificity_indicator}
- **URL**: {paper.get('url', 'N/A')}
"""
        
        # Specificity distribution
        specificity_ranges = {
            'Ultra-Specific (0.8-1.0)': 0,
            'Highly Specific (0.6-0.8)': 0
        }
        
        for paper in papers:
            score = paper['specificity_score']
            if score >= 0.8:
                specificity_ranges['Ultra-Specific (0.8-1.0)'] += 1
            else:
                specificity_ranges['Highly Specific (0.6-0.8)'] += 1
        
        report += f"\n## 📊 Specificity Distribution:\n"
        for range_name, count in specificity_ranges.items():
            percentage = (count / len(papers) * 100) if papers else 0
            report += f"- **{range_name}**: {count} papers ({percentage:.1f}%)\n"
        
        report += f"""

## 🔍 Search Strategy Analysis:
- **Query parts identified**: {', '.join(specificity_analysis['query_components']['main_parts'])}
- **Key terms extracted**: {', '.join(specificity_analysis['query_components']['all_terms'])}
- **Search approach**: Ultra-specific matching prioritizing complete query coverage
- **Filtering**: Only papers with ≥60% specificity to your exact query included

## 🎯 Ultra-Specific Insights:
- **Specificity Focus**: Papers ranked by how well they match your COMPLETE query
- **No Generic Papers**: Filtered out broad reviews and general topic papers
- **Exact Matches Prioritized**: Papers containing your exact phrase combinations ranked highest
- **Quality Balance**: Specificity (70%) + Citations (20%) + Journal (10%)

## 💡 Recommendations:
- Focus on 🎯 ultra-specific papers for most relevant insights
- These papers directly address your specific research question
- Avoid generic papers that only match individual keywords
- Consider the complete context of your query in these results

---

*Report generated by Ultra-Specific Research AI Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Papers filtered and ranked by specificity to your complete query*
"""
        
        return report

def main():
    """Main function for ultra-specific research"""
    print("🎯 Ultra-Specific Research AI Agent")
    print("Finds papers that match your COMPLETE query, not just sub-topics!")
    print("Filters out generic papers and prioritizes exact matches")
    print("=" * 60)
    
    agent = UltraSpecificResearchAgent()
    
    while True:
        try:
            query = input("\n📝 Enter your specific research query (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                print("Please enter a valid query.")
                continue
            
            # Ask for number of papers
            while True:
                try:
                    max_papers_input = input("📊 How many ultra-specific papers do you want? (default: 30, max recommended: 50): ").strip()
                    if not max_papers_input:
                        max_papers = 30
                        break
                    max_papers = int(max_papers_input)
                    if max_papers <= 0:
                        print("Please enter a positive number.")
                        continue
                    if max_papers > 100:
                        print("⚠️  Warning: Large requests may take time and may not improve specificity.")
                        confirm = input("Continue? (y/n): ").strip().lower()
                        if confirm not in ['y', 'yes']:
                            continue
                    break
                except ValueError:
                    print("Please enter a valid number.")
            
            # Generate ultra-specific research report
            report = agent.research_topic(query, max_papers)
            print("\n" + "="*60)
            print("🎯 ULTRA-SPECIFIC RESEARCH REPORT")
            print("="*60)
            print(report)
            
            # Ask if user wants to save
            save = input("\n💾 Save report to file? (y/n): ").strip().lower()
            if save in ['y', 'yes']:
                filename = f"ultra_specific_report_{query.replace(' ', '_')[:30]}_{max_papers}papers.txt"
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
