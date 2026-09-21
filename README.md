# ResearchLens

An NLP-Based Research Discovery, Literature Analysis and Research Landscape Mapping Platform.

Enter a research topic → automatically discover 10–15 relevant papers → analyze them using NLP → get an interactive research landscape and structured report.

## Features

- Automatic paper discovery via Semantic Scholar API
- NLP preprocessing (tokenization, lemmatization, POS tagging)
- TF-IDF keyword extraction
- Named Entity Recognition + custom research dictionaries
- Semantic similarity using sentence-transformers
- Paper clustering (K-Means)
- Research trend analysis
- Methodology comparison
- Semantic search across papers
- Interactive dashboard with charts
- Downloadable structured research report

## Tech Stack

- **Backend**: Python + Flask
- **Database**: SQLite
- **NLP**: spaCy + scikit-learn
- **Embeddings**: sentence-transformers
- **Frontend**: HTML + CSS + JavaScript + Chart.js
- **Paper API**: Semantic Scholar

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python app.py
```

Then open `http://localhost:5000` in your browser.
