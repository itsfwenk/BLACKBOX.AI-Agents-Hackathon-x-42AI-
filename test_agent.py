#!/usr/bin/env python3
"""
Simple test script for the Research AI Agent using only standard library
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime

def test_semantic_scholar_api():
    """Test basic connectivity to Semantic Scholar API"""
    print("🔍 Testing Semantic Scholar API...")
    
    try:
        query = "machine learning"
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit=5&fields=paperId,title,authors,year,citationCount"
        
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
        papers = data.get('data', [])
        print(f"✅ Successfully retrieved {len(papers)} papers")
        
        if papers:
            print("\nSample results:")
            for i, paper in enumerate(papers[:3], 1):
                title = paper.get('title', 'Unknown Title')
                year = paper.get('year', 'Unknown')
                citations = paper.get('citationCount', 0)
                authors = [author.get('name', 'Unknown') for author in paper.get('authors', [])]
                
                print(f"\n{i}. {title}")
                print(f"   Authors: {', '.join(authors[:2])}")
                print(f"   Year: {year}")
                print(f"   Citations: {citations:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Semantic Scholar API: {e}")
        return False

def test_arxiv_api():
    """Test basic connectivity to arXiv API"""
    print("\n🔍 Testing arXiv API...")
    
    try:
        query = "machine learning"
        encoded_query = urllib.parse.quote(f'all:{query}')
        url = f"http://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results=3"
        
        with urllib.request.urlopen(url) as response:
            xml_data = response.read().decode()
        
        # Simple XML parsing without external libraries
        entries = xml_data.count('<entry>')
        print(f"✅ Successfully retrieved {entries} papers from arXiv")
        
        # Extract first title (simple string parsing)
        if '<title>' in xml_data:
            start = xml_data.find('<title>') + 7
            end = xml_data.find('</title>', start)
            first_title = xml_data[start:end].strip()
            print(f"\nSample paper: {first_title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing arXiv API: {e}")
        return False

def main():
    """Run basic API tests"""
    print("🤖 Research AI Agent - Basic API Test")
    print("=" * 50)
    
    # Test APIs
    ss_success = test_semantic_scholar_api()
    arxiv_success = test_arxiv_api()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Semantic Scholar API: {'✅ Working' if ss_success else '❌ Failed'}")
    print(f"arXiv API: {'✅ Working' if arxiv_success else '❌ Failed'}")
    
    if ss_success or arxiv_success:
        print("\n🎉 At least one API is working! The agent should function properly.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the full agent: python main.py 'your research query'")
    else:
        print("\n⚠️ No APIs are accessible. Check your internet connection.")

if __name__ == "__main__":
    main()
