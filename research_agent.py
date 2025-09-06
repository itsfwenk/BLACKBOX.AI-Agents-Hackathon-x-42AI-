"""
Main Research AI Agent class
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from paper_search import PaperSearcher
from config import Config

class ResearchAgent:
    def __init__(self):
        self.config = Config()
        self.paper_searcher = PaperSearcher()
        self.config.validate_config()
        
    def research_topic(self, query: str, output_format: str = None) -> Dict:
        """
        Main method to research a topic and establish state of the art
        """
        if output_format is None:
            output_format = self.config.DEFAULT_OUTPUT_FORMAT
            
        print(f"🤖 Research Agent starting analysis of: '{query}'")
        print("=" * 60)
        
        # Step 1: Search for papers
        search_results = self.paper_searcher.search_papers(query)
        
        if search_results['total_papers'] == 0:
            return {
                'query': query,
                'status': 'no_results',
                'message': 'No papers found for the given query.',
                'timestamp': datetime.now().isoformat()
            }
        
        # Step 2: Analyze and synthesize findings
        synthesis = self._synthesize_findings(search_results)
        
        # Step 3: Generate state-of-the-art report
        report = self._generate_report(query, search_results, synthesis, output_format)
        
        return {
            'query': query,
            'status': 'success',
            'total_papers_analyzed': search_results['total_papers'],
            'synthesis': synthesis,
            'report': report,
            'raw_data': search_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _synthesize_findings(self, search_results: Dict) -> Dict:
        """
        Synthesize findings from the paper search results
        """
        print("🧠 Synthesizing research findings...")
        
        papers = search_results['papers']
        analysis = search_results['analysis']
        
        # Key insights
        insights = {
            'research_maturity': self._assess_research_maturity(analysis),
            'key_contributors': self._identify_key_contributors(papers),
            'research_trends': self._identify_trends(analysis),
            'methodological_approaches': self._analyze_methodologies(papers),
            'knowledge_gaps': self._identify_gaps(papers, analysis)
        }
        
        return insights
    
    def _assess_research_maturity(self, analysis: Dict) -> Dict:
        """Assess the maturity level of the research area"""
        total_papers = len(analysis.get('most_cited', []))
        avg_citations = analysis.get('average_citations', 0)
        year_span = self._calculate_year_span(analysis.get('year_distribution', {}))
        
        if avg_citations > 100 and year_span > 10:
            maturity = "Mature"
            description = "Well-established research area with significant citation history"
        elif avg_citations > 50 and year_span > 5:
            maturity = "Developing"
            description = "Growing research area with increasing attention"
        elif avg_citations > 10 and year_span > 2:
            maturity = "Emerging"
            description = "New research area gaining traction"
        else:
            maturity = "Early Stage"
            description = "Very new or niche research area"
        
        return {
            'level': maturity,
            'description': description,
            'average_citations': avg_citations,
            'research_span_years': year_span
        }
    
    def _identify_key_contributors(self, papers: List[Dict]) -> List[Dict]:
        """Identify key contributors/authors in the field"""
        author_stats = {}
        
        for paper in papers:
            for author in paper.get('authors', []):
                if author not in author_stats:
                    author_stats[author] = {
                        'name': author,
                        'paper_count': 0,
                        'total_citations': 0,
                        'papers': []
                    }
                
                author_stats[author]['paper_count'] += 1
                author_stats[author]['total_citations'] += paper.get('citation_count', 0)
                author_stats[author]['papers'].append({
                    'title': paper['title'],
                    'year': paper.get('year'),
                    'citations': paper.get('citation_count', 0)
                })
        
        # Sort by impact (combination of paper count and citations)
        key_authors = sorted(
            author_stats.values(),
            key=lambda x: x['paper_count'] * 2 + x['total_citations'] / 100,
            reverse=True
        )[:10]
        
        return key_authors
    
    def _identify_trends(self, analysis: Dict) -> Dict:
        """Identify research trends over time"""
        year_dist = analysis.get('year_distribution', {})
        recent_papers = analysis.get('recent_papers', [])
        
        # Calculate growth trend
        if len(year_dist) >= 3:
            years = sorted(year_dist.keys(), reverse=True)
            recent_avg = sum(year_dist[year] for year in years[:3]) / 3
            older_avg = sum(year_dist[year] for year in years[3:6]) / min(3, len(years[3:6])) if len(years) > 3 else recent_avg
            
            if recent_avg > older_avg * 1.5:
                trend = "Rapidly Growing"
            elif recent_avg > older_avg * 1.1:
                trend = "Growing"
            elif recent_avg < older_avg * 0.8:
                trend = "Declining"
            else:
                trend = "Stable"
        else:
            trend = "Insufficient Data"
        
        # Identify hot topics from recent papers
        recent_keywords = self._extract_keywords_from_titles([p['title'] for p in recent_papers])
        
        return {
            'publication_trend': trend,
            'recent_hot_topics': recent_keywords[:10],
            'peak_year': max(year_dist.keys(), key=lambda k: year_dist[k]) if year_dist else None
        }
    
    def _analyze_methodologies(self, papers: List[Dict]) -> List[str]:
        """Analyze common methodologies mentioned in papers"""
        methodology_keywords = [
            'machine learning', 'deep learning', 'neural network', 'algorithm',
            'experiment', 'simulation', 'survey', 'review', 'meta-analysis',
            'case study', 'empirical', 'theoretical', 'statistical', 'optimization',
            'reinforcement learning', 'supervised learning', 'unsupervised learning',
            'natural language processing', 'computer vision', 'data mining'
        ]
        
        method_counts = {}
        for paper in papers:
            title_abstract = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()
            for method in methodology_keywords:
                if method in title_abstract:
                    method_counts[method] = method_counts.get(method, 0) + 1
        
        return sorted(method_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _identify_gaps(self, papers: List[Dict], analysis: Dict) -> List[str]:
        """Identify potential research gaps"""
        gaps = []
        
        # Check for lack of recent highly-cited work
        recent_papers = analysis.get('recent_papers', [])
        if recent_papers and max(p.get('citation_count', 0) for p in recent_papers) < 50:
            gaps.append("Limited high-impact recent publications - opportunity for breakthrough work")
        
        # Check venue diversity
        top_venues = analysis.get('top_venues', [])
        if len(top_venues) < 3:
            gaps.append("Research concentrated in few venues - opportunity for interdisciplinary work")
        
        # Check for methodological diversity
        methodologies = self._analyze_methodologies(papers)
        if len(methodologies) < 5:
            gaps.append("Limited methodological diversity - opportunity for novel approaches")
        
        return gaps
    
    def _generate_report(self, query: str, search_results: Dict, synthesis: Dict, format_type: str) -> str:
        """Generate a comprehensive state-of-the-art report"""
        if format_type == "markdown":
            return self._generate_markdown_report(query, search_results, synthesis)
        elif format_type == "json":
            return json.dumps({
                'query': query,
                'search_results': search_results,
                'synthesis': synthesis
            }, indent=2)
        else:
            return self._generate_text_report(query, search_results, synthesis)
    
    def _generate_markdown_report(self, query: str, search_results: Dict, synthesis: Dict) -> str:
        """Generate a markdown-formatted report"""
        analysis = search_results['analysis']
        
        report = f"""# State of the Art: {query}

## Executive Summary

This report analyzes **{search_results['total_papers']} papers** to establish the current state of the art in "{query}".

**Research Maturity**: {synthesis['research_maturity']['level']} - {synthesis['research_maturity']['description']}

**Publication Trend**: {synthesis['research_trends']['publication_trend']}

---

## Most Cited Papers (Foundational Work)

"""
        
        for i, paper in enumerate(analysis['most_cited'][:5], 1):
            authors_str = ", ".join(paper['authors'][:3])
            if len(paper['authors']) > 3:
                authors_str += " et al."
            
            report += f"""### {i}. {paper['title']}
- **Authors**: {authors_str}
- **Year**: {paper.get('year', 'Unknown')}
- **Citations**: {paper['citation_count']:,}
- **Venue**: {paper.get('venue', 'Unknown')}
- **URL**: {paper.get('url', 'N/A')}

"""
            if paper.get('abstract'):
                abstract = paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract']
                report += f"**Abstract**: {abstract}\n\n"

        report += """---

## Recent Developments (Last 3 Years)

"""
        
        for i, paper in enumerate(analysis['recent_papers'][:5], 1):
            authors_str = ", ".join(paper['authors'][:3])
            if len(paper['authors']) > 3:
                authors_str += " et al."
            
            report += f"""### {i}. {paper['title']}
- **Authors**: {authors_str}
- **Year**: {paper.get('year', 'Unknown')}
- **Citations**: {paper['citation_count']:,}
- **Venue**: {paper.get('venue', 'Unknown')}

"""

        report += """---

## Key Contributors

"""
        
        for i, author in enumerate(synthesis['key_contributors'][:5], 1):
            report += f"""### {i}. {author['name']}
- **Papers in this area**: {author['paper_count']}
- **Total citations**: {author['total_citations']:,}
- **Most cited work**: {max(author['papers'], key=lambda x: x['citations'])['title']} ({max(author['papers'], key=lambda x: x['citations'])['citations']} citations)

"""

        report += """---

## Research Trends & Hot Topics

"""
        
        trends = synthesis['research_trends']
        report += f"""**Current Trend**: {trends['publication_trend']}

**Emerging Topics** (from recent papers):
"""
        
        for topic, count in trends['recent_hot_topics']:
            report += f"- {topic} (mentioned in {count} papers)\n"

        report += """

---

## Methodological Approaches

"""
        
        for method, count in synthesis['methodological_approaches']:
            report += f"- **{method.title()}**: {count} papers\n"

        report += """

---

## Research Gaps & Opportunities

"""
        
        for gap in synthesis['knowledge_gaps']:
            report += f"- {gap}\n"

        report += f"""

---

## Summary Statistics

- **Total Papers Analyzed**: {search_results['total_papers']:,}
- **Total Citations**: {analysis['total_citations']:,}
- **Average Citations per Paper**: {analysis['average_citations']:.1f}
- **Top Venues**: {', '.join([venue for venue, count in analysis['top_venues'][:3]])}
- **Research Span**: {min(analysis['year_distribution'].keys()) if analysis['year_distribution'] else 'Unknown'} - {max(analysis['year_distribution'].keys()) if analysis['year_distribution'] else 'Unknown'}

---

*Report generated by Research AI Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report
    
    def _generate_text_report(self, query: str, search_results: Dict, synthesis: Dict) -> str:
        """Generate a plain text report"""
        # Simplified version of the markdown report without formatting
        return self._generate_markdown_report(query, search_results, synthesis).replace('#', '').replace('**', '').replace('*', '')
    
    def _calculate_year_span(self, year_distribution: Dict) -> int:
        """Calculate the span of years in the research"""
        if not year_distribution:
            return 0
        years = list(year_distribution.keys())
        return max(years) - min(years) if years else 0
    
    def _extract_keywords_from_titles(self, titles: List[str]) -> List[tuple]:
        """Extract common keywords from paper titles"""
        # Simple keyword extraction - could be enhanced with NLP
        word_counts = {}
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        for title in titles:
            words = title.lower().split()
            for word in words:
                # Clean word
                word = ''.join(c for c in word if c.isalnum())
                if len(word) > 3 and word not in stop_words:
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        return sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
