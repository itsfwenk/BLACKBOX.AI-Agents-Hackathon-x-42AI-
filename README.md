# Research Paper Discovery AI Agent

An intelligent AI agent that analyzes research topics and establishes the state of the art by discovering the most cited papers, recent developments, key contributors, and research trends.

## 🚀 Features

- **Comprehensive Paper Search**: Integrates with Semantic Scholar and arXiv APIs
- **State-of-the-Art Analysis**: Identifies foundational and recent breakthrough papers
- **Research Synthesis**: Analyzes trends, key contributors, and methodological approaches
- **Multiple Output Formats**: Markdown, JSON, and plain text reports
- **Interactive CLI**: Rich command-line interface with progress tracking
- **Research Gap Identification**: Highlights opportunities for future research

## 📋 Requirements

- Python 3.8+
- Internet connection for API access
- Optional: OpenAI API key for enhanced summarization

## 🛠️ Installation

1. **Clone or download the project files**

2. **Set up a virtual environment** (recommended):
```bash
python -m venv research_agent_env
source research_agent_env/bin/activate  # On Windows: research_agent_env\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment** (optional):
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key if you have one
```

## 🎯 Quick Start

### Simple Usage
```bash
# Basic research query
python main.py "machine learning interpretability"

# Research a medical topic
python main.py "CRISPR gene editing"

# Explore quantum computing
python main.py "quantum computing algorithms"
```

### Advanced CLI Usage
```bash
# Full research with markdown output
python cli.py research "transformer neural networks"

# Save report to file
python cli.py research "federated learning" --output report.md

# JSON output for programmatic use
python cli.py research "blockchain scalability" --format json

# Interactive mode with follow-up questions
python cli.py research "natural language processing" --interactive

# Quick search without full analysis
python cli.py quick "deep learning" --limit 10

# Check system status
python cli.py status --check-apis
```

## 📊 What the Agent Analyzes

### Paper Discovery
- **Most Cited Papers**: Foundational works that shaped the field
- **Recent Developments**: Latest papers from the past 3 years
- **Influential Papers**: Works with high impact beyond citation count

### Research Insights
- **Key Contributors**: Leading researchers and their contributions
- **Publication Trends**: Growth patterns and research momentum
- **Methodological Approaches**: Common techniques and frameworks
- **Research Gaps**: Opportunities for future work

### Venue Analysis
- **Top Journals/Conferences**: Where the best work is published
- **Publication Timeline**: Historical development of the field

## 📈 Sample Output

The agent generates comprehensive reports like this:

```markdown
# State of the Art: Machine Learning Interpretability

## Executive Summary
This report analyzes **47 papers** to establish the current state of the art in "machine learning interpretability".

**Research Maturity**: Developing - Growing research area with increasing attention
**Publication Trend**: Rapidly Growing

## Most Cited Papers (Foundational Work)

### 1. LIME: Explaining the predictions of any machine learning classifier
- **Authors**: Marco Tulio Ribeiro, Sameer Singh, Carlos Guestrin
- **Year**: 2016
- **Citations**: 8,234
- **Venue**: KDD

### 2. SHAP: A Unified Approach to Explaining Machine Learning Model Predictions
- **Authors**: Scott M. Lundberg, Su-In Lee
- **Year**: 2017
- **Citations**: 6,891
- **Venue**: NIPS

[... continues with detailed analysis ...]
```

## 🔧 Configuration

The agent can be configured via `config.py`:

```python
# Search Parameters
MAX_PAPERS_PER_QUERY = 50
MIN_CITATION_COUNT = 5
RECENT_YEARS_THRESHOLD = 3

# Output Settings
DEFAULT_OUTPUT_FORMAT = "markdown"
MAX_ABSTRACT_LENGTH = 500
```

## 🌐 API Integration

### Semantic Scholar API
- **Primary source** for academic papers
- **No API key required**
- Provides citation counts, abstracts, author info

### arXiv API
- **Preprint source** for latest research
- **No API key required**
- Covers computer science, physics, math, biology

### OpenAI API (Optional)
- **Enhanced summarization** capabilities
- Requires API key
- Improves research synthesis quality

## 📝 Example Queries

### Computer Science
- "transformer neural networks"
- "federated learning privacy"
- "graph neural networks"
- "reinforcement learning robotics"

### Medicine & Biology
- "CRISPR gene editing"
- "COVID-19 vaccine development"
- "cancer immunotherapy"
- "Alzheimer's disease biomarkers"

### Physics & Engineering
- "quantum computing algorithms"
- "renewable energy storage"
- "autonomous vehicle safety"
- "climate change modeling"

### Social Sciences
- "social media mental health"
- "remote work productivity"
- "artificial intelligence ethics"
- "educational technology effectiveness"

## 🔍 Interactive Features

The CLI supports interactive mode where you can ask follow-up questions:

```bash
python cli.py research "deep learning" --interactive

# Then ask questions like:
❓ Your question: Tell me more about the key authors
❓ Your question: What are the main publication venues?
❓ Your question: What research gaps did you identify?
```

## 🚨 Troubleshooting

### Common Issues

1. **No papers found**
   - Try broader search terms
   - Check internet connection
   - Verify API endpoints are accessible

2. **Rate limiting errors**
   - The agent includes built-in delays
   - If issues persist, increase `API_DELAY_SECONDS` in config

3. **Missing dependencies**
   - Ensure all packages in `requirements.txt` are installed
   - Try upgrading pip: `pip install --upgrade pip`

### Check System Status
```bash
python cli.py status --check-apis
```

## 🤝 Contributing

The agent is designed to be extensible:

- **Add new APIs**: Extend `PaperSearcher` class
- **Enhance analysis**: Modify `ResearchAgent` synthesis methods
- **Improve CLI**: Add new commands to `cli.py`
- **Custom outputs**: Create new report formats

## 📄 License

This project is open source. Feel free to use, modify, and distribute.

## 🙏 Acknowledgments

- **Semantic Scholar** for providing free academic paper API
- **arXiv** for open access to preprints
- **Rich** library for beautiful CLI interfaces

---

*Built with ❤️ for the research community*
