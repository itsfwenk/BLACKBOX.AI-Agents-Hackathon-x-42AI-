#!/usr/bin/env python3
"""
Journal-Aware Research AI Agent - Prioritizes papers from top journals in the field
Enhanced with multi-source search: Semantic Scholar, PubMed, arXiv, CrossRef
"""
import requests
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
from typing import List, Dict, Optional, Set
import re

class JournalAwareConfig:
    # API Endpoints
    SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
    ARXIV_API_BASE = "http://export.arxiv.org/api/query"
    CROSSREF_API_BASE = "https://api.crossref.org/works"
    PUBMED_API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # Search Parameters
    DEFAULT_MAX_PAPERS = 100
    API_DELAY_SECONDS = 1
    
    # Top journals by field - curated list of high-impact venues
    TOP_JOURNALS = {
        # Computer Science & AI
        'computer_science': {
            'Nature', 'Science', 'Nature Machine Intelligence', 'Nature Communications',
            'Proceedings of the National Academy of Sciences', 'PNAS',
            'Journal of Machine Learning Research', 'JMLR',
            'IEEE Transactions on Pattern Analysis and Machine Intelligence', 'TPAMI',
            'International Conference on Machine Learning', 'ICML',
            'Neural Information Processing Systems', 'NeurIPS', 'NIPS',
            'International Conference on Learning Representations', 'ICLR',
            'Association for Computational Linguistics', 'ACL',
            'IEEE Transactions on Neural Networks and Learning Systems',
            'Artificial Intelligence', 'Journal of Artificial Intelligence Research',
            'Computer Vision and Pattern Recognition', 'CVPR',
            'International Conference on Computer Vision', 'ICCV',
            'European Conference on Computer Vision', 'ECCV'
        },
        
        # Medicine & Biology
        'medicine': {
            'Nature', 'Science', 'Cell', 'The Lancet', 'New England Journal of Medicine',
            'Nature Medicine', 'Nature Biotechnology', 'Nature Genetics',
            'Journal of the American Medical Association', 'JAMA',
            'British Medical Journal', 'BMJ', 'PLOS Medicine',
            'Nature Reviews Drug Discovery', 'Nature Reviews Genetics',
            'Proceedings of the National Academy of Sciences', 'PNAS',
            'Nature Communications', 'Science Translational Medicine',
            'Cell Metabolism', 'Cell Stem Cell', 'Immunity',
            'Journal of Clinical Investigation', 'Blood', 'Cancer Cell'
        },
        
        # Biology & Life Sciences
        'biology': {
            'Nature', 'Science', 'Cell', 'Nature Communications',
            'Proceedings of the National Academy of Sciences', 'PNAS',
            'Nature Biotechnology', 'Nature Genetics', 'Nature Cell Biology',
            'Molecular Cell', 'Developmental Cell', 'Current Biology',
            'PLOS Biology', 'eLife', 'Journal of Cell Biology',
            'Nature Structural & Molecular Biology', 'Nature Methods',
            'Genome Research', 'Nature Reviews Molecular Cell Biology',
            'Trends in Cell Biology', 'Annual Review of Cell and Developmental Biology'
        },
        
        # Physics
        'physics': {
            'Nature', 'Science', 'Nature Physics', 'Nature Photonics',
            'Physical Review Letters', 'Reviews of Modern Physics',
            'Nature Materials', 'Advanced Materials',
            'Proceedings of the National Academy of Sciences', 'PNAS',
            'Physical Review X', 'Science Advances',
            'Nature Nanotechnology', 'Nano Letters',
            'Physical Review A', 'Physical Review B', 'Physical Review D'
        },
        
        # Chemistry
        'chemistry': {
            'Nature', 'Science', 'Nature Chemistry', 'Nature Catalysis',
            'Journal of the American Chemical Society', 'JACS',
            'Angewandte Chemie International Edition',
            'Chemical Reviews', 'Accounts of Chemical Research',
            'Nature Materials', 'Advanced Materials',
            'Proceedings of the National Academy of Sciences', 'PNAS',
            'Chemical Science', 'ACS Catalysis', 'Organic Letters'
        },
        
        # Engineering
        'engineering': {
            'Nature', 'Science', 'Nature Materials', 'Nature Energy',
            'Proceedings of the National Academy of Sciences', 'PNAS',
            'Advanced Materials', 'Advanced Functional Materials',
            'IEEE Transactions', 'Nature Electronics',
            'Science Advances', 'Energy & Environmental Science',
            'Nature Nanotechnology', 'Nano Letters'
        },
        
        # Social Sciences
        'social_science': {
            'Nature', 'Science', 'Nature Human Behaviour',
            'Proceedings of the National Academy of Sciences', 'PNAS',
            'Psychological Science', 'American Psychologist',
            'Journal of Personality and Social Psychology',
            'Psychological Review', 'Annual Review of Psychology',
            'Science Advances', 'Nature Communications'
        }
    }

class JournalAwarePaperSearcher:
    def __init__(self):
        self.config = JournalAwareConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-AI-Agent/1.0'
        })
    
    def _identify_research_field(self, query: str) -> Set[str]:
        """Identify the research field(s) based on the query"""
        query_lower = query.lower()
        
        # Keywords that indicate different fields
        field_keywords = {
            'computer_science': [
                'machine learning', 'deep learning', 'neural network', 'artificial intelligence',
                'computer vision', 'natural language processing', 'nlp', 'algorithm',
                'data mining', 'reinforcement learning', 'transformer', 'cnn', 'rnn',
                'computer science', 'software', 'programming', 'ai', 'ml'
            ],
            'medicine': [
                'disease', 'treatment', 'therapy', 'clinical', 'patient', 'medical',
                'drug', 'vaccine', 'cancer', 'diabetes', 'covid', 'virus', 'bacteria',
                'pathogen', 'antibiotic', 'pharmaceutical', 'medicine', 'health',
                'diagnosis', 'symptom', 'epidemic', 'pandemic'
            ],
            'biology': [
                'gene', 'protein', 'cell', 'dna', 'rna', 'genome', 'genetic',
                'molecular', 'biology', 'organism', 'species', 'evolution',
                'ecology', 'biodiversity', 'enzyme', 'metabolism', 'cellular',
                'biotechnology', 'bioinformatics', 'phylogeny', 'microbe'
            ],
            'physics': [
                'quantum', 'particle', 'physics', 'energy', 'matter', 'force',
                'electromagnetic', 'thermodynamics', 'mechanics', 'relativity',
                'photon', 'electron', 'atom', 'nuclear', 'plasma', 'optics',
                'condensed matter', 'theoretical physics'
            ],
            'chemistry': [
                'chemical', 'chemistry', 'molecule', 'compound', 'reaction',
                'synthesis', 'catalyst', 'organic', 'inorganic', 'analytical',
                'physical chemistry', 'biochemistry', 'polymer', 'material'
            ],
            'engineering': [
                'engineering', 'design', 'system', 'technology', 'manufacturing',
                'mechanical', 'electrical', 'civil', 'chemical engineering',
                'materials science', 'nanotechnology', 'robotics', 'automation'
            ],
            'social_science': [
                'psychology', 'sociology', 'behavior', 'social', 'human',
                'cognitive', 'mental health', 'education', 'economics',
                'political', 'anthropology', 'linguistics', 'culture'
            ]
        }
        
        identified_fields = set()
        
        for field, keywords in field_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    identified_fields.add(field)
        
        # If no specific field identified, default to general high-impact journals
        if not identified_fields:
            identified_fields.add('computer_science')  # Default fallback
        
        return identified_fields
    
    def _get_top_journals_for_query(self, query: str) -> Set[str]:
        """Get the set of top journals relevant to the query"""
        fields = self._identify_research_field(query)
        
        top_journals = set()
        for field in fields:
            if field in self.config.TOP_JOURNALS:
                top_journals.update(self.config.TOP_JOURNALS[field])
        
        return top_journals
    
    def _calculate_journal_score(self, venue: str, top_journals: Set[str]) -> int:
        """Calculate a score for the journal/venue (higher = better)"""
        if not venue:
            return 0
        
        venue_clean = venue.strip()
        
        # Exact match with top journals
        if venue_clean in top_journals:
            return 100
        
        # Partial match (case insensitive)
        venue_lower = venue_clean.lower()
        for top_journal in top_journals:
            if top_journal.lower() in venue_lower or venue_lower in top_journal.lower():
                return 80
        
        # High-impact indicators
        high_impact_indicators = [
            'nature', 'science', 'cell', 'lancet', 'jama', 'bmj', 'pnas',
            'proceedings of the national academy', 'ieee transactions',
            'journal of the american', 'annual review', 'reviews of modern'
        ]
        
        for indicator in high_impact_indicators:
            if indicator in venue_lower:
                return 60
        
        # Conference proceedings (lower priority than journals)
        conference_indicators = ['conference', 'proceedings', 'workshop', 'symposium']
        for indicator in conference_indicators:
            if indicator in venue_lower:
                return 40
        
        # arXiv preprints
        if venue_lower == 'arxiv':
            return 20
        
        # Default score for other venues
        return 10
    
    def search_papers(self, query: str, max_results: int = None, per_source_limit: int = None) -> Dict:
        """Search for papers using multiple sources, prioritizing top journals"""
        if max_results is None:
            max_results = self.config.DEFAULT_MAX_PAPERS
        
        if per_source_limit is None:
            per_source_limit = max(max_results // 4, 10)
        
        # Identify top journals for this query
        top_journals = self._get_top_journals_for_query(query)
        identified_fields = self._identify_research_field(query)
        
        print(f"🔍 Searching for papers on: '{query}'")
        print(f"🎯 Identified research fields: {', '.join(identified_fields)}")
        print(f"📊 Target: {max_results} total papers ({per_source_limit} per source)")
        print(f"🏆 Prioritizing {len(top_journals)} top journals in the field")
        print("=" * 60)
        
        # Search all sources
        semantic_papers = self._search_semantic_scholar(query, per_source_limit)
        pubmed_papers = self._search_pubmed_improved(query, per_source_limit)
        arxiv_papers = self._search_arxiv(query, per_source_limit)
        crossref_papers = self._search_crossref(query, per_source_limit)
        
        # Combine and deduplicate
        all_papers = self._combine_and_deduplicate(
            semantic_papers, pubmed_papers, arxiv_papers, crossref_papers
        )
        
        # Score papers based on journal quality and citations
        for paper in all_papers:
            venue = paper.get('venue', '')
            journal_score = self._calculate_journal_score(venue, top_journals)
            citation_score = min(paper.get('citation_count', 0) / 10, 50)  # Cap at 50
            
            # Combined score: journal quality (60%) + citations (40%)
            paper['quality_score'] = journal_score * 0.6 + citation_score * 0.4
            paper['is_top_journal'] = journal_score >= 80
        
        # Sort by quality score (journal + citations), then by year
        all_papers.sort(key=lambda x: (x['quality_score'], x.get('year') or 0), reverse=True)
        
        # Limit to max_results
        if len(all_papers) > max_results:
            all_papers = all_papers[:max_results]
        
        # Count papers from top journals
        top_journal_count = sum(1 for p in all_papers if p.get('is_top_journal', False))
        
        return {
            'query': query,
            'total_papers': len(all_papers),
            'papers': all_papers,
            'sources_used': ['Semantic Scholar', 'PubMed', 'arXiv', 'CrossRef'],
            'search_timestamp': datetime.now().isoformat(),
            'search_params': {
                'max_results': max_results,
                'per_source_limit': per_source_limit
            },
            'journal_analysis': {
                'identified_fields': list(identified_fields),
                'top_journals_count': len(top_journals),
                'papers_from_top_journals': top_journal_count,
                'top_journal_percentage': (top_journal_count / len(all_papers) * 100) if all_papers else 0
            }
        }
    
    def _search_semantic_scholar(self, query: str, limit: int) -> List[Dict]:
        """Search Semantic Scholar API"""
        try:
            actual_limit = min(limit, 100)
            
            url = f"{self.config.SEMANTIC_SCHOLAR_API_BASE}/paper/search"
            params = {
                'query': query,
                'limit': actual_limit,
                'fields': 'paperId,title,authors,year,citationCount,abstract,url,venue,publicationVenue'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for paper in data.get('data', []):
                # Get venue from multiple possible fields
                venue = paper.get('venue', '')
                if not venue and paper.get('publicationVenue'):
                    venue = paper.get('publicationVenue', {}).get('name', '')
                
                papers.append({
                    'title': paper.get('title', 'Unknown Title'),
                    'authors': [author.get('name', 'Unknown') for author in paper.get('authors', [])],
                    'year': paper.get('year'),
                    'citation_count': paper.get('citationCount', 0),
                    'abstract': paper.get('abstract', ''),
                    'source': 'Semantic Scholar',
                    'url': paper.get('url', ''),
                    'venue': venue
                })
            
            print(f"✅ Found {len(papers)} papers from Semantic Scholar (requested: {actual_limit})")
            time.sleep(self.config.API_DELAY_SECONDS)
            return papers
            
        except Exception as e:
            print(f"❌ Error searching Semantic Scholar: {e}")
            return []
    
    def _search_pubmed_improved(self, query: str, limit: int) -> List[Dict]:
        """Improved PubMed search with better query handling"""
        try:
            actual_limit = min(limit, 200)
            
            # Format query for PubMed
            pubmed_query = query.replace(' and ', ' AND ').replace(' or ', ' OR ')
            
            search_url = f"{self.config.PUBMED_API_BASE}/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': pubmed_query,
                'retmax': actual_limit,
                'retmode': 'json',
                'sort': 'relevance'
            }
            
            search_response = self.session.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            pmids = search_data.get('esearchresult', {}).get('idlist', [])
            if not pmids:
                # Try alternative search strategies
                alt_strategies = [
                    ' OR '.join(query.split()),
                    f'"{query}"'
                ]
                
                for alt_query in alt_strategies:
                    search_params['term'] = alt_query
                    search_response = self.session.get(search_url, params=search_params)
                    search_data = search_response.json()
                    pmids = search_data.get('esearchresult', {}).get('idlist', [])
                    if pmids:
                        break
                    time.sleep(0.5)
            
            if not pmids:
                print(f"✅ Found 0 papers from PubMed")
                return []
            
            time.sleep(self.config.API_DELAY_SECONDS)
            
            # Fetch detailed information
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
                            'citation_count': 0,  # PubMed doesn't provide citation counts
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

class JournalAwareResearchAgent:
    def __init__(self):
        self.searcher = JournalAwarePaperSearcher()
    
    def research_topic(self, query: str, max_papers: int = 100) -> str:
        """Research a topic prioritizing top journals in the field"""
        print(f"🤖 Journal-Aware Research Agent analyzing: '{query}'")
        print(f"🎯 Target: {max_papers} papers from top journals")
        print("=" * 60)
        
        # Search for papers
        results = self.searcher.search_papers(query, max_results=max_papers)
        
        if results['total_papers'] == 0:
            return "No papers found for the given query."
        
        # Generate report
        report = self._generate_journal_aware_report(results)
        return report
    
    def _generate_journal_aware_report(self, results: Dict) -> str:
        """Generate a report emphasizing journal quality"""
        papers = results['papers']
        journal_analysis = results['journal_analysis']
        
        # Separate papers by journal tier
        top_journal_papers = [p for p in papers if p.get('is_top_journal', False)]
        other_papers = [p for p in papers if not p.get('is_top_journal', False)]
        
        # Most cited papers (regardless of journal)
        most_cited = sorted([p for p in papers if p['citation_count'] > 0], 
                           key=lambda x: x['citation_count'], reverse=True)[:10]
        
        # Recent papers from top journals
        recent_top_papers = sorted([p for p in top_journal_papers if p['year'] and p['year'] >= 2020], 
                                  key=lambda x: x['year'] or 0, reverse=True)[:10]
        
        # Count by source
        sources = {}
        for paper in papers:
            source = paper['source']
            sources[source] = sources.get(source, 0) + 1
        
        report = f"""
# Journal-Aware Research Report: {results['query']}

## Summary
- **Total papers analyzed**: {results['total_papers']:,}
- **Research fields identified**: {', '.join(journal_analysis['identified_fields'])}
- **Papers from top journals**: {journal_analysis['papers_from_top_journals']} ({journal_analysis['top_journal_percentage']:.1f}%)
- **Top journals considered**: {journal_analysis['top_journals_count']}
- **Sources searched**: {', '.join(results['sources_used'])}
- **Search completed**: {results['search_timestamp'][:19]}

## Papers by Source:
"""
        for source, count in sources.items():
            report += f"- **{source}**: {count} papers\n"
        
        if top_journal_papers:
            report += f"\n## 🏆 Papers from Top-Tier Journals ({len(top_journal_papers)} papers):\n"
            for i, paper in enumerate(top_journal_papers[:10], 1):
                authors_str = ", ".join(paper['authors'][:3])
                if len(paper['authors']) > 3:
                    authors_str += " et al."
                
                report += f"""
### {i}. {paper['title']}
- **Authors**: {authors_str}
- **Journal**: {paper.get('venue', 'N/A')} 🏆
- **Year**: {paper.get('year', 'N/A')} | **Citations**: {paper['citation_count']:,} | **Source**: {paper['source']}
- **Quality Score**: {paper.get('quality_score', 0):.1f}/100
- **URL**: {paper.get('url', 'N/A')}
"""
        
        report += "\n## 📈 Most Cited Papers (All Sources):\n"
        for i, paper in enumerate(most_cited, 1):
            authors_str = ", ".join(paper['authors'][:3])
            if len(paper['authors']) > 3:
                authors_str += " et al."
            
            journal_indicator = " 🏆" if paper.get('is_top_journal', False) else ""
            
            report += f"""
### {i}. {paper['title']}
- **Authors**: {authors_str}
- **Journal**: {paper.get('venue', 'N/A')}{journal_indicator}
- **Year**: {paper.get('year', 'N/A')} | **Citations**: {paper['citation_count']:,} | **Source**: {paper['source']}
- **Quality Score**: {paper.get('quality_score', 0):.1f}/100
- **URL**: {paper.get('url', 'N/A')}
"""
        
        if recent_top_papers:
            report += f"\n## 🆕 Recent Papers from Top Journals (2020+):\n"
            for i, paper in enumerate(recent_top_papers, 1):
                authors_str = ", ".join(paper['authors'][:2])
                if len(paper['authors']) > 2:
                    authors_str += " et al."
                
                report += f"""
### {i}. {paper['title']}
- **Authors**: {authors_str}
- **Journal**: {paper.get('venue', 'N/A')} 🏆
- **Year**: {paper.get('year', 'N/A')} | **Source**: {paper['source']}
- **Quality Score**: {paper.get('quality_score', 0):.1f}/100
- **URL**: {paper.get('url', 'N/A')}
"""
        
        # Journal quality analysis
        venue_scores = {}
        for paper in papers:
            venue = paper.get('venue', 'Unknown')
            if venue not in venue_scores:
                venue_scores[venue] = {
                    'count': 0,
                    'avg_citations': 0,
                    'is_top': paper.get('is_top_journal', False),
                    'total_citations': 0
                }
            venue_scores[venue]['count'] += 1
            venue_scores[venue]['total_citations'] += paper.get('citation_count', 0)
        
        # Calculate averages
        for venue_data in venue_scores.values():
            if venue_data['count'] > 0:
                venue_data['avg_citations'] = venue_data['total_citations'] / venue_data['count']
        
        # Sort venues by quality (top journals first, then by average citations)
        sorted_venues = sorted(venue_scores.items(), 
                              key=lambda x: (x[1]['is_top'], x[1]['avg_citations']), 
                              reverse=True)
        
        report += f"\n## 📊 Journal Quality Analysis:\n"
        for venue, data in sorted_venues[:10]:
            tier_indicator = " 🏆" if data['is_top'] else ""
            report += f"- **{venue}**{tier_indicator}: {data['count']} papers, avg {data['avg_citations']:.1f} citations\n"
        
        report += f"""

## 🎯 Research Quality Insights:
- **{journal_analysis['top_journal_percentage']:.1f}%** of papers are from top-tier journals
- **Field coverage**: {', '.join(journal_analysis['identified_fields'])}
- **Quality prioritization**: Papers ranked by journal impact + citation count
- **Recommendation**: Focus on the 🏆 top-tier journal papers for highest quality insights

---

*Report generated by Journal-Aware Research AI Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Papers prioritized by journal reputation and citation impact*
"""
        
        return report

def main():
    """Main function for journal-aware research"""
    print("🏆 Journal-Aware Research AI Agent")
    print("Prioritizes papers from top journals in your field!")
    print("Searches: Semantic Scholar, PubMed, arXiv, CrossRef")
    print("=" * 60)
    
    agent = JournalAwareResearchAgent()
    
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
            print("🏆 JOURNAL-AWARE RESEARCH REPORT")
            print("="*60)
            print(report)
            
            # Ask if user wants to save
            save = input("\n💾 Save report to file? (y/n): ").strip().lower()
            if save in ['y', 'yes']:
                filename = f"journal_report_{query.replace(' ', '_')[:30]}_{max_papers}papers.txt"
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
