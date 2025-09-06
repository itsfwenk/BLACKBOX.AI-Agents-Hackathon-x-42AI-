# Enhanced Research AI Agent - Usage Guide

## 🎯 What's New: Multi-Source Research Coverage

Your Research AI Agent has been **significantly enhanced** to search across **4 major academic databases** instead of just 2:

### 📚 **Data Sources**
1. **Semantic Scholar** - Comprehensive academic database with citation metrics
2. **PubMed** - Medical and life sciences literature (NCBI database)
3. **arXiv** - Preprints in CS, Physics, Mathematics, and more
4. **CrossRef** - DOI-indexed academic papers across all disciplines

This enhancement provides **comprehensive coverage** across all research domains, especially medical and life sciences research through PubMed integration.

---

## 🚀 Quick Start

### 1. Basic Usage (Simple Interface)
```bash
python3 main.py
```
Then enter your research query when prompted.

### 2. Command Line Interface (Advanced Features)
```bash
# Basic research with markdown report
python3 cli.py research "machine learning interpretability"

# Save results to file
python3 cli.py research "COVID-19 vaccine effectiveness" --output report.md

# JSON output for programmatic use
python3 cli.py research "quantum computing" --format json

# Interactive mode with follow-up questions
python3 cli.py research "natural language processing" --interactive

# Quick search without full analysis
python3 cli.py quick "deep learning" --limit 10
```

---

## 📊 Example Queries by Domain

### 🧬 **Medical & Life Sciences** (leverages PubMed)
- "COVID-19 vaccine effectiveness"
- "CRISPR gene editing applications"
- "cancer immunotherapy mechanisms"
- "Alzheimer's disease biomarkers"
- "diabetes treatment innovations"

### 💻 **Computer Science** (leverages arXiv + Semantic Scholar)
- "transformer neural networks"
- "federated learning privacy"
- "graph neural networks applications"
- "reinforcement learning robotics"
- "computer vision object detection"

### 🔬 **Physics & Engineering** (leverages arXiv + CrossRef)
- "quantum computing algorithms"
- "renewable energy storage systems"
- "autonomous vehicle safety"
- "climate change modeling"
- "materials science nanotechnology"

### 🧠 **Interdisciplinary Research** (leverages all sources)
- "artificial intelligence ethics"
- "social media mental health impact"
- "educational technology effectiveness"
- "blockchain healthcare applications"

---

## 📈 Sample Output

When you run a query like `"COVID-19 vaccine effectiveness"`, you'll get:

```
🔍 Searching for papers on: 'COVID-19 vaccine effectiveness'
✅ Found 15 papers from PubMed
✅ Found 15 papers from arXiv  
✅ Found 8 papers from CrossRef
⚠️ Semantic Scholar (rate limited - will retry)

📊 RESULTS SUMMARY
Total papers found: 38
Sources used: PubMed, arXiv, CrossRef, Semantic Scholar

📈 PAPERS BY SOURCE:
  • PubMed: 15 papers (medical literature)
  • arXiv: 15 papers (preprints & research)
  • CrossRef: 8 papers (peer-reviewed journals)
```

---

## 🛠️ Installation & Setup

### Option 1: Direct Usage (No Setup Required)
The agent works with Python's standard libraries and external APIs. Just run:
```bash
python3 main.py
```

### Option 2: Full Setup with Dependencies
```bash
# Create virtual environment (optional)
python3 -m venv research_env
source research_env/bin/activate  # Linux/Mac
# or
research_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run with full features
python3 cli.py research "your query here"
```

### Option 3: Environment Configuration (Optional)
Create a `.env` file for API keys (optional - most APIs work without keys):
```bash
cp .env.example .env
# Edit .env to add any API keys you have
```

---

## 🎯 Key Features

### ✅ **Multi-Source Integration**
- Searches 4 major academic databases simultaneously
- Automatic deduplication across sources
- Minimum 10 papers per source for comprehensive coverage

### ✅ **Intelligent Analysis**
- Citation-based ranking (most influential papers)
- Recency filtering (latest developments)
- Research trend identification
- Gap analysis and opportunities
- Key contributor identification

### ✅ **Flexible Output**
- **Markdown**: Beautiful formatted reports
- **JSON**: Programmatic access to data
- **Text**: Plain text for simple use
- **Interactive**: Follow-up questions and exploration

### ✅ **Robust Error Handling**
- API rate limiting protection
- Graceful fallback when sources are unavailable
- Network error recovery
- Malformed data handling

---

## 🔧 Advanced Usage

### Custom Search Limits
```bash
python3 cli.py research "your query" --max-papers 100
```

### Check System Status
```bash
python3 cli.py status --check-apis
```

### View Examples
```bash
python3 cli.py examples
```

### Interactive Mode Features
When using `--interactive`, you can ask follow-up questions like:
- "Tell me more about the authors"
- "What are the top venues?"
- "Show me the research trends"
- "What are the knowledge gaps?"

---

## 📋 Output Structure

### Markdown Report Includes:
1. **Executive Summary** - Research maturity and trends
2. **Most Cited Papers** - Foundational work with high impact
3. **Recent Developments** - Latest papers (last 3 years)
4. **Key Contributors** - Leading researchers in the field
5. **Research Trends** - Publication patterns and hot topics
6. **Methodological Approaches** - Common research methods
7. **Research Gaps** - Opportunities for future work
8. **Summary Statistics** - Comprehensive metrics

---

## 🚨 Important Notes

### API Rate Limits
- **Semantic Scholar**: May hit rate limits with frequent use (handled gracefully)
- **PubMed**: Generally reliable, 3 requests per second limit
- **arXiv**: Very reliable, no strict limits
- **CrossRef**: Reliable, polite usage recommended

### Data Coverage
- **PubMed**: Excellent for medical/life sciences (40M+ papers)
- **arXiv**: Best for preprints and cutting-edge research
- **Semantic Scholar**: Broad academic coverage with citation metrics
- **CrossRef**: Comprehensive DOI-indexed papers

### Performance
- Typical query: 10-30 seconds for 40-60 papers
- Large queries (100+ papers): 1-2 minutes
- Network dependent - faster with good connection

---

## 🎉 Success! Your Enhanced Research AI Agent

You now have a **powerful multi-source research discovery tool** that:

✅ **Searches 4 major academic databases** (including PubMed as requested)  
✅ **Provides comprehensive coverage** across all research domains  
✅ **Delivers real paper data** with proper titles, authors, and abstracts  
✅ **Handles errors gracefully** with rate limiting and fallback mechanisms  
✅ **Offers flexible interfaces** from simple to advanced usage  

**Ready to discover the state of the art in any research field!** 🚀
