"""
Command-line interface for the Research AI Agent
"""
import click
import json
import os
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from research_agent import ResearchAgent

console = Console()

@click.group()
def cli():
    """Research AI Agent - Discover state-of-the-art papers and research trends"""
    pass

@cli.command()
@click.argument('query')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'text']), 
              default='markdown', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Save output to file')
@click.option('--max-papers', '-m', type=int, default=50, 
              help='Maximum number of papers to analyze')
@click.option('--interactive', '-i', is_flag=True, 
              help='Interactive mode with follow-up questions')
def research(query, format, output, max_papers, interactive):
    """Research a topic and generate state-of-the-art analysis"""
    
    console.print(Panel.fit(
        f"🤖 Research AI Agent\n\nAnalyzing: [bold cyan]{query}[/bold cyan]",
        border_style="blue"
    ))
    
    # Initialize agent
    agent = ResearchAgent()
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Searching and analyzing papers...", total=None)
        
        # Perform research
        results = agent.research_topic(query, output_format=format)
    
    if results['status'] == 'no_results':
        console.print(f"[red]❌ {results['message']}[/red]")
        return
    
    # Display results
    if format == 'json':
        output_content = json.dumps(results, indent=2)
        if not output:
            console.print(output_content)
    else:
        output_content = results['report']
        if format == 'markdown' and not output:
            console.print(Markdown(output_content))
        elif not output:
            console.print(output_content)
    
    # Save to file if specified
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(output_content)
        console.print(f"[green]✅ Report saved to {output}[/green]")
    
    # Show summary statistics
    _display_summary_stats(results)
    
    # Interactive mode
    if interactive:
        _interactive_mode(agent, results)

@cli.command()
@click.argument('query')
@click.option('--limit', '-l', type=int, default=10, help='Number of papers to show')
def quick(query, limit):
    """Quick search for papers without full analysis"""
    
    console.print(f"🔍 Quick search for: [bold]{query}[/bold]")
    
    agent = ResearchAgent()
    search_results = agent.paper_searcher.search_papers(query, max_results=limit)
    
    if search_results['total_papers'] == 0:
        console.print("[red]❌ No papers found[/red]")
        return
    
    # Display papers in a table
    table = Table(title=f"Papers for '{query}'")
    table.add_column("Title", style="cyan", no_wrap=False, max_width=50)
    table.add_column("Authors", style="magenta", max_width=30)
    table.add_column("Year", justify="center")
    table.add_column("Citations", justify="right", style="green")
    table.add_column("Venue", style="yellow", max_width=20)
    
    for paper in search_results['papers'][:limit]:
        authors = ", ".join(paper['authors'][:2])
        if len(paper['authors']) > 2:
            authors += " et al."
        
        table.add_row(
            paper['title'][:100] + "..." if len(paper['title']) > 100 else paper['title'],
            authors,
            str(paper.get('year', 'N/A')),
            f"{paper['citation_count']:,}",
            paper.get('venue', 'N/A')[:20]
        )
    
    console.print(table)

@cli.command()
def examples():
    """Show example queries and use cases"""
    
    examples_text = """
# Example Queries

Here are some example research queries you can try:

## Computer Science
- "transformer neural networks"
- "federated learning privacy"
- "graph neural networks"
- "reinforcement learning robotics"

## Medicine & Biology
- "CRISPR gene editing"
- "COVID-19 vaccine development"
- "cancer immunotherapy"
- "Alzheimer's disease biomarkers"

## Physics & Engineering
- "quantum computing algorithms"
- "renewable energy storage"
- "autonomous vehicle safety"
- "climate change modeling"

## Social Sciences
- "social media mental health"
- "remote work productivity"
- "artificial intelligence ethics"
- "educational technology effectiveness"

## Usage Examples

```bash
# Basic research with markdown output
python cli.py research "machine learning interpretability"

# Save results to file
python cli.py research "quantum computing" --output quantum_report.md

# JSON output for programmatic use
python cli.py research "blockchain scalability" --format json

# Interactive mode for follow-up questions
python cli.py research "natural language processing" --interactive

# Quick search without full analysis
python cli.py quick "deep learning" --limit 5
```
    """
    
    console.print(Markdown(examples_text))

@cli.command()
@click.option('--check-apis', is_flag=True, help='Check API connectivity')
def status(check_apis):
    """Check system status and configuration"""
    
    console.print(Panel.fit("🔧 System Status", border_style="green"))
    
    # Check configuration
    from config import Config
    config = Config()
    
    status_table = Table(title="Configuration Status")
    status_table.add_column("Component", style="cyan")
    status_table.add_column("Status", justify="center")
    status_table.add_column("Details", style="dim")
    
    # Check OpenAI API key
    openai_status = "✅ Configured" if config.OPENAI_API_KEY else "⚠️ Not configured"
    openai_details = "Summarization available" if config.OPENAI_API_KEY else "Limited summarization"
    status_table.add_row("OpenAI API", openai_status, openai_details)
    
    # Check API endpoints
    if check_apis:
        import requests
        
        # Test Semantic Scholar
        try:
            response = requests.get(f"{config.SEMANTIC_SCHOLAR_API_BASE}/paper/search?query=test&limit=1", timeout=5)
            ss_status = "✅ Online" if response.status_code == 200 else "❌ Error"
        except:
            ss_status = "❌ Offline"
        
        # Test arXiv
        try:
            response = requests.get(f"{config.ARXIV_API_BASE}?search_query=test&max_results=1", timeout=5)
            arxiv_status = "✅ Online" if response.status_code == 200 else "❌ Error"
        except:
            arxiv_status = "❌ Offline"
        
        status_table.add_row("Semantic Scholar API", ss_status, "Primary paper source")
        status_table.add_row("arXiv API", arxiv_status, "Preprint source")
    
    console.print(status_table)

def _display_summary_stats(results):
    """Display summary statistics"""
    stats_table = Table(title="Analysis Summary")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", justify="right", style="green")
    
    stats_table.add_row("Papers Analyzed", f"{results['total_papers_analyzed']:,}")
    
    if 'synthesis' in results:
        maturity = results['synthesis']['research_maturity']
        stats_table.add_row("Research Maturity", maturity['level'])
        stats_table.add_row("Avg Citations", f"{maturity['average_citations']:.1f}")
        
        trends = results['synthesis']['research_trends']
        stats_table.add_row("Publication Trend", trends['publication_trend'])
    
    console.print(stats_table)

def _interactive_mode(agent, results):
    """Interactive mode for follow-up questions"""
    console.print("\n[bold blue]🤖 Interactive Mode[/bold blue]")
    console.print("Ask follow-up questions about the research. Type 'quit' to exit.\n")
    
    while True:
        question = console.input("[bold cyan]❓ Your question: [/bold cyan]")
        
        if question.lower() in ['quit', 'exit', 'q']:
            console.print("[yellow]👋 Goodbye![/yellow]")
            break
        
        # Simple question handling - could be enhanced with NLP
        if 'author' in question.lower():
            _show_author_details(results)
        elif 'venue' in question.lower() or 'journal' in question.lower():
            _show_venue_details(results)
        elif 'trend' in question.lower():
            _show_trend_details(results)
        elif 'gap' in question.lower():
            _show_gap_details(results)
        else:
            console.print("[yellow]💡 Try asking about: authors, venues, trends, or gaps[/yellow]")

def _show_author_details(results):
    """Show detailed author information"""
    if 'synthesis' in results and 'key_contributors' in results['synthesis']:
        authors = results['synthesis']['key_contributors'][:5]
        
        table = Table(title="Key Authors")
        table.add_column("Author", style="cyan")
        table.add_column("Papers", justify="center")
        table.add_column("Citations", justify="right", style="green")
        table.add_column("Most Cited Work", style="dim")
        
        for author in authors:
            most_cited = max(author['papers'], key=lambda x: x['citations'])
            table.add_row(
                author['name'],
                str(author['paper_count']),
                f"{author['total_citations']:,}",
                most_cited['title'][:50] + "..."
            )
        
        console.print(table)

def _show_venue_details(results):
    """Show venue/journal details"""
    if 'raw_data' in results and 'analysis' in results['raw_data']:
        venues = results['raw_data']['analysis'].get('top_venues', [])
        
        table = Table(title="Top Publication Venues")
        table.add_column("Venue", style="cyan")
        table.add_column("Papers", justify="right", style="green")
        
        for venue, count in venues:
            table.add_row(venue, str(count))
        
        console.print(table)

def _show_trend_details(results):
    """Show detailed trend information"""
    if 'synthesis' in results and 'research_trends' in results['synthesis']:
        trends = results['synthesis']['research_trends']
        
        console.print(f"[bold]Publication Trend:[/bold] {trends['publication_trend']}")
        
        if 'recent_hot_topics' in trends:
            console.print("\n[bold]Hot Topics:[/bold]")
            for topic, count in trends['recent_hot_topics'][:5]:
                console.print(f"  • {topic} ({count} mentions)")

def _show_gap_details(results):
    """Show research gaps"""
    if 'synthesis' in results and 'knowledge_gaps' in results['synthesis']:
        gaps = results['synthesis']['knowledge_gaps']
        
        console.print("[bold]Research Gaps & Opportunities:[/bold]")
        for i, gap in enumerate(gaps, 1):
            console.print(f"  {i}. {gap}")

if __name__ == '__main__':
    cli()
