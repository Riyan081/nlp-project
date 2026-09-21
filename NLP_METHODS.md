# NLP Methods Used in ResearchLens

This document explains all the Natural Language Processing (NLP) methods and techniques used in this project. Each section covers **what** the technique is, **why** we use it, and **where** in the code it's implemented.

---

## Table of Contents

1. [Text Preprocessing (spaCy)](#1-text-preprocessing-spacy)
2. [TF-IDF Keyword Extraction](#2-tf-idf-keyword-extraction)
3. [Named Entity Recognition (NER)](#3-named-entity-recognition-ner)
4. [POS Tagging](#4-pos-tagging)
5. [Dictionary-Based Information Extraction](#5-dictionary-based-information-extraction)
6. [Sentence Embeddings (Transformer-Based)](#6-sentence-embeddings-transformer-based)
7. [Cosine Similarity](#7-cosine-similarity)
8. [K-Means Clustering](#8-k-means-clustering)
9. [Semantic Search](#9-semantic-search)
10. [Research Gap Analysis](#10-research-gap-analysis)

---

## 1. Text Preprocessing (spaCy)

**File:** `services/nlp.py`  
**Library:** spaCy (`en_core_web_sm` model)

### What it does
Before any NLP analysis, raw paper abstracts go through a preprocessing pipeline:
- **Tokenization** — Splits text into individual words/tokens
- **Lemmatization** — Reduces words to their base form (e.g., "forecasting" → "forecast", "models" → "model")
- **Stop Word Removal** — Removes common words like "the", "is", "and" that don't carry meaning
- **Sentence Segmentation** — Splits text into individual sentences

### Why we use it
Raw text is messy. Preprocessing normalizes it so that NLP algorithms can work more accurately. For example, without lemmatization, "predict", "predicts", and "predicting" would be treated as three different words.

### Code snippet
```python
doc = nlp(text)  # spaCy processes the text
tokens = [token.text for token in doc if not token.is_space]
lemmas = [token.lemma_.lower() for token in doc 
          if not token.is_stop and not token.is_punct and not token.is_space]
sentences = [sent.text.strip() for sent in doc.sents]
```

---

## 2. TF-IDF Keyword Extraction

**File:** `services/nlp.py`  
**Library:** scikit-learn (`TfidfVectorizer`)

### What it does
TF-IDF (Term Frequency–Inverse Document Frequency) identifies the most important keywords in each paper and across all papers.

- **TF (Term Frequency)** — How often a word appears in one document
- **IDF (Inverse Document Frequency)** — How rare a word is across ALL documents
- **TF-IDF = TF × IDF** — Words that are frequent in one paper but rare across others get high scores

### Why we use it
TF-IDF finds keywords that are **distinctive** to each paper, not just common words. For example, in a set of ML papers, the word "learning" appears everywhere (low IDF), but "XGBoost" might only appear in one paper (high IDF), making it a more meaningful keyword.

### Two levels of extraction
1. **Per-paper keywords** — Top 20 keywords for each individual paper (unigrams + bigrams)
2. **Global keywords** — Top 30 keywords across all papers combined (unigrams + bigrams + trigrams)

### Code snippet
```python
vectorizer = TfidfVectorizer(
    max_features=500,
    stop_words='english',
    ngram_range=(1, 3),  # unigrams, bigrams, trigrams
    min_df=1,
    max_df=0.95,
)
tfidf_matrix = vectorizer.fit_transform(abstracts)
```

### Parameters explained
| Parameter | Value | Meaning |
|-----------|-------|---------|
| `max_features` | 500 | Only consider top 500 terms |
| `stop_words` | 'english' | Remove common English words |
| `ngram_range` | (1, 3) | Extract single words, 2-word phrases, and 3-word phrases |
| `min_df` | 1 | Term must appear in at least 1 document |
| `max_df` | 0.95 | Ignore terms appearing in >95% of documents |

---

## 3. Named Entity Recognition (NER)

**File:** `services/nlp.py`  
**Library:** spaCy (`en_core_web_sm`)

### What it does
NER automatically identifies and classifies named entities in text into categories like:
- **ORG** — Organizations (e.g., "IEEE", "Google")
- **GPE** — Geopolitical entities / locations (e.g., "China", "Europe")
- **DATE** — Dates and time periods (e.g., "2023", "last decade")
- **PERSON** — People's names
- **CARDINAL** — Numbers

### Why we use it
NER helps us automatically discover which organizations, locations, and datasets are mentioned across research papers without manually reading each one.

### Code snippet
```python
for ent in doc.ents:
    entities.append({
        'text': ent.text.strip(),       # The entity text
        'label': ent.label_,             # Category (ORG, GPE, etc.)
        'description': spacy.explain(ent.label_),  # Human-readable label
    })
```

---

## 4. POS Tagging

**File:** `services/nlp.py`  
**Library:** spaCy

### What it does
POS (Part-of-Speech) tagging assigns grammatical labels to each word:
- **NOUN** — nouns (model, data, algorithm)
- **VERB** — verbs (predict, train, evaluate)
- **ADJ** — adjectives (accurate, robust, novel)

### Why we use it
POS tagging helps us understand the linguistic structure of abstracts. It's used internally by spaCy for better NER and dependency parsing accuracy.

### Code snippet
```python
pos_tags = [
    {'token': token.text, 'pos': token.pos_, 'tag': token.tag_}
    for token in doc if not token.is_space
]
```

---

## 5. Dictionary-Based Information Extraction

**File:** `services/nlp.py` + `config.py`

### What it does
We maintain curated dictionaries of:
- **Research Methods** (42 methods) — e.g., "random forest", "LSTM", "XGBoost", "transformer"
- **Datasets** (16 entries) — e.g., "MNIST", "ImageNet", "CIFAR"
- **Evaluation Metrics** (18 metrics) — e.g., "RMSE", "F1-score", "accuracy", "AUC"

The system scans each paper's abstract against these dictionaries using case-insensitive string matching.

### Why we use it
Pure NER can't reliably detect domain-specific terms like "XGBoost" or "RMSE" because they're not in general-purpose NER models. Dictionary matching ensures we catch these important research-specific terms.

### Code snippet
```python
def _extract_from_dictionary(text, dictionary):
    text_lower = text.lower()
    found = []
    for term in dictionary:
        if term.lower() in text_lower:
            found.append(term)
    return found
```

---

## 6. Sentence Embeddings (Transformer-Based)

**File:** `services/similarity.py`  
**Library:** sentence-transformers  
**Model:** `all-MiniLM-L6-v2`

### What it does
Converts each paper's abstract into a **384-dimensional dense vector** (embedding) that captures its semantic meaning. Papers about similar topics will have similar vectors, even if they use different words.

### How it works
The `all-MiniLM-L6-v2` model is a distilled version of BERT (a transformer model) fine-tuned for sentence similarity tasks. It:
1. Tokenizes the text into subword tokens
2. Passes tokens through 6 transformer layers with attention mechanisms
3. Pools the output into a single 384-dim vector

### Why we use it
Traditional methods (like TF-IDF) compare exact words. Embeddings understand **meaning**. For example:
- "electricity demand prediction" and "power consumption forecasting" have no words in common
- But their embeddings will be very similar because they mean the same thing

### Code snippet
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(abstracts, show_progress_bar=False)
# Result: numpy array of shape (num_papers, 384)
```

### Model details
| Property | Value |
|----------|-------|
| Model | all-MiniLM-L6-v2 |
| Base | Microsoft MiniLM (distilled BERT) |
| Embedding dimension | 384 |
| Max input length | 256 tokens |
| Training | Trained on 1B+ sentence pairs |

---

## 7. Cosine Similarity

**File:** `services/similarity.py`  
**Library:** scikit-learn (`cosine_similarity`)

### What it does
Measures how similar two paper embeddings are by computing the cosine of the angle between their vectors. The result ranges from:
- **1.0** — Identical meaning
- **0.0** — Completely unrelated
- **-1.0** — Opposite meaning (rare in practice)

### Formula
```
similarity(A, B) = (A · B) / (||A|| × ||B||)
```

Where `A · B` is the dot product and `||A||` is the vector magnitude.

### Why we use it
Cosine similarity is the standard metric for comparing text embeddings because it's:
- **Scale-invariant** — doesn't depend on document length
- **Fast to compute** — simple linear algebra
- **Interpretable** — 0.8 means "very similar", 0.3 means "somewhat related"

### Code snippet
```python
from sklearn.metrics.pairwise import cosine_similarity
sim_matrix = cosine_similarity(vectors)  # Returns NxN matrix
```

### Output
We build an **N×N similarity matrix** where `matrix[i][j]` is the similarity between paper i and paper j. This is visualized as a heatmap in the dashboard.

---

## 8. K-Means Clustering

**File:** `services/analysis.py`  
**Library:** scikit-learn (`KMeans`)

### What it does
Groups papers into **clusters** (research themes) based on their embeddings. Papers with similar content end up in the same cluster.

### How K-Means works
1. Pick K random cluster centers (centroids)
2. Assign each paper to the nearest centroid
3. Recalculate centroids as the mean of assigned papers
4. Repeat steps 2–3 until stable (convergence)

### Why we use it
Clustering reveals the main **research themes** in a corpus automatically. For example, in "ML for Electricity Demand Forecasting", clusters might be:
- Cluster 1: Deep learning approaches (LSTM, CNN)
- Cluster 2: Statistical methods (ARIMA, exponential smoothing)
- Cluster 3: Ensemble methods (XGBoost, Random Forest)

### Parameters
| Parameter | Value | Meaning |
|-----------|-------|---------|
| `n_clusters` | 3 (default, max 5) | Number of groups to create |
| `random_state` | 42 | Reproducible results |
| `n_init` | 10 | Run 10 times with different seeds, pick best |

### Cluster labeling
Each cluster gets a human-readable label from its top TF-IDF keywords. We also list the methods used in each cluster.

### Code snippet
```python
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
labels = kmeans.fit_predict(embedding_vectors)
# labels = [0, 1, 0, 2, 1, ...] — cluster assignment for each paper
```

---

## 9. Semantic Search

**File:** `services/similarity.py`

### What it does
Lets users type a natural language query (e.g., "papers about weather data") and finds the most relevant papers using embedding similarity — not keyword matching.

### How it works
1. Encode the user's query with the same `all-MiniLM-L6-v2` model
2. Compute cosine similarity between the query embedding and all paper embeddings
3. Return papers ranked by similarity score

### Why we use it
Traditional keyword search only finds exact word matches. Semantic search understands meaning:
- Query: "deep learning models" → also finds papers about "neural networks", "CNN", "LSTM"
- Query: "renewable energy forecasting" → finds papers about "solar prediction", "wind power estimation"

### Code snippet
```python
query_embedding = model.encode([query])
similarities = cosine_similarity(query_embedding, paper_embeddings)[0]
# Sort by similarity, return top results
```

---

## 10. Research Gap Analysis

**File:** `services/analysis.py`

### What it does
Identifies gaps in the research literature by combining multiple analysis techniques:

### Gap Types

| Gap Type | Method | What it detects |
|----------|--------|----------------|
| **Underexplored Methods** | Frequency analysis | Methods appearing in <15% of papers |
| **Declining Themes** | Temporal analysis | Keywords present in older papers but absent in recent 2 years |
| **Cross-Cluster Gaps** | Cluster comparison | Methods isolated to a single research cluster |
| **Isolated Papers** | Similarity analysis | Papers with low avg similarity to others (unique angles) |
| **Unexplored Combinations** | Co-occurrence analysis | Popular methods that are never used together |

### Why we use it
Research gap analysis helps researchers identify **where future work is needed**. It's computed automatically from the NLP analysis results.

---

## Architecture Overview

```
User enters topic
        ↓
   Paper Search (Semantic Scholar / OpenAlex API)
        ↓
   ┌─────────────────────────────────────────────────┐
   │              NLP Analysis Pipeline              │
   │                                                 │
   │  1. spaCy Preprocessing (tokenize, lemmatize)   │
   │  2. TF-IDF Keyword Extraction                   │
   │  3. Named Entity Recognition (NER)              │
   │  4. POS Tagging                                 │
   │  5. Dictionary-based Method/Dataset Extraction   │
   │  6. Sentence Embeddings (MiniLM transformer)    │
   │  7. Cosine Similarity Matrix                    │
   │  8. K-Means Clustering                          │
   │  9. Trend Analysis (temporal)                   │
   │ 10. Research Gap Analysis                       │
   └─────────────────────────────────────────────────┘
        ↓
   Interactive Dashboard + Research Report
```

---

## Libraries & Models

| Library | Version | Purpose |
|---------|---------|---------|
| **spaCy** | 3.x | Tokenization, NER, POS tagging, lemmatization |
| **scikit-learn** | 1.x | TF-IDF, K-Means clustering, cosine similarity |
| **sentence-transformers** | 3.x | BERT-based sentence embeddings |
| **Flask** | 3.x | Web framework |
| **SQLite** | built-in | Database storage |
| **Chart.js** | 4.x | Frontend charts and visualizations |

| Model | Type | Purpose |
|-------|------|---------|
| `en_core_web_sm` | spaCy pipeline | English NLP (tokenizer + NER + POS) |
| `all-MiniLM-L6-v2` | Sentence Transformer | 384-dim semantic embeddings |

---

## Summary

This project combines **classical NLP** (TF-IDF, NER, POS tagging) with **modern deep learning** (transformer embeddings, semantic search) and **unsupervised ML** (K-Means clustering) to automatically analyze research papers. The pipeline processes raw text → extracts structured information → computes semantic relationships → identifies research patterns and gaps.
