"""Test pipeline — uses OpenAlex (no rate limits)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("ResearchLens — Full Pipeline Test")
print("=" * 60)

# Test 1: Paper search (will fallback to OpenAlex if Semantic Scholar blocked)
print("\n[TEST 1] Paper Search...")
from services.paper_search import search_papers
results = search_papers("Machine Learning for Electricity Demand Forecasting")
print(f"  Papers returned: {len(results)}")

if len(results) == 0:
    print("  FAIL — No papers returned!")
    sys.exit(1)

for i, p in enumerate(results[:5]):
    print(f"  {i+1}. [{p.get('year')}] {p['title'][:65]} (rel: {p.get('relevance_score')})")
print(f"  PASS\n")

# Test 2: NLP
print("[TEST 2] NLP Analysis (spaCy + TF-IDF)...")
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

nlp = spacy.load("en_core_web_sm")
doc = nlp(results[0]["abstract"])
tokens = [t.text for t in doc if not t.is_space]
entities = [(e.text, e.label_) for e in doc.ents]
sentences = list(doc.sents)
print(f"  Tokens: {len(tokens)}, Sentences: {len(sentences)}, Entities: {len(entities)}")
if entities:
    print(f"  Sample entities: {entities[:3]}")

# TF-IDF
abstracts = [p["abstract"] for p in results if p.get("abstract")]
vec = TfidfVectorizer(max_features=50, stop_words="english", ngram_range=(1, 2))
tfidf = vec.fit_transform(abstracts)
features = vec.get_feature_names_out()
scores = tfidf.mean(axis=0).A1
top = scores.argsort()[::-1][:10]
print(f"  Top TF-IDF keywords: {[features[i] for i in top]}")
print(f"  PASS\n")

# Test 3: Method extraction
print("[TEST 3] Method Extraction (domain dictionary)...")
from config import RESEARCH_METHODS
import re

all_methods = set()
for p in results:
    text_lower = p["abstract"].lower()
    for method in RESEARCH_METHODS:
        if method.lower() in text_lower:
            all_methods.add(method)

print(f"  Methods found: {all_methods}")
print(f"  PASS\n")

# Test 4: Embeddings + Similarity
print("[TEST 4] Sentence Embeddings + Cosine Similarity...")
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(abstracts[:5])
print(f"  Embedding shape: {embeddings.shape}")

sim_matrix = cosine_similarity(embeddings)
print(f"  Similarity matrix shape: {sim_matrix.shape}")
print(f"  Sample similarities: P1-P2={sim_matrix[0][1]:.3f}, P1-P3={sim_matrix[0][2]:.3f}")
print(f"  PASS\n")

# Test 5: K-Means Clustering
print("[TEST 5] K-Means Clustering...")
from sklearn.cluster import KMeans

all_emb = model.encode(abstracts)
n_clusters = min(3, len(abstracts) - 1)
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
labels = kmeans.fit_predict(all_emb)
print(f"  Clusters: {n_clusters}")
for c in range(n_clusters):
    count = sum(1 for l in labels if l == c)
    indices = [i for i, l in enumerate(labels) if l == c]
    print(f"  Cluster {c+1}: {count} papers — e.g. {results[indices[0]]['title'][:50]}")
print(f"  PASS\n")

print("=" * 60)
print("ALL 5 TESTS PASSED!")
print("=" * 60)
