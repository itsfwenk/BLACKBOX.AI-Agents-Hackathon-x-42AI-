#!/usr/bin/env python3
"""
Main entry point for the Research AI Agent
"""
import sys
import os
from research_agent import ResearchAgent
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    """Main function for direct usage"""
    if len(sys.argv) < 2:
        console.print(Panel.fit(
            """🤖 Research AI Agent

Usage:
  python main.py "your research query"
  
Examples:
  python main.py "machine learning interpretability"
  python main.py "quantum computing algorithms"
  python main.py "CRISPR gene editing"

For more options, use the CLI:
  python cli.py --help
            """,
            title="Research AI Agent",
            border_style="blue"
        ))
        return
    
    query = " ".join(sys.argv[1:])
    
    console.print(f"🔍 Researching: [bold cyan]{query}[/bold cyan]")
    
    try:
        agent = ResearchAgent()
        results = agent.research_topic(query)
        
        if results['status'] == 'success':
            console.print("\n" + "="*80)
            console.print(results['report'])
        else:
            console.print(f"[red]❌ {results.get('message', 'Unknown error')}[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        console.print("\nTip: Make sure you have an internet connection and try again.")

if __name__ == "__main__":
    main()
