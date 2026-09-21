import re
import json
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import database
from config import (
    SPACY_MODEL, TOP_KEYWORDS, TOP_GLOBAL_KEYWORDS,
    RESEARCH_METHODS, RESEARCH_DATASETS, RESEARCH_METRICS
)

# Load spaCy model (loaded once when module is first imported)
try:
    nlp = spacy.load(SPACY_MODEL)
except OSError:
    print(f"spaCy model '{SPACY_MODEL}' not found. Run: python -m spacy download {SPACY_MODEL}")
    nlp = None


def analyze_papers(session_id, papers):
    """
    Run full NLP analysis on all papers in a session.
    Returns a list of analysis dicts.
    """
    if not nlp:
        print("spaCy model not loaded. Skipping NLP analysis.")
        return []

    abstracts = [p.get('abstract', '') for p in papers]

    # Step 1: TF-IDF across all papers
    global_keywords = _extract_global_keywords(abstracts)

    # Step 2: Per-paper analysis
    analyses = []
    for i, paper in enumerate(papers):
        abstract = paper.get('abstract', '')
        if not abstract:
            analyses.append(_empty_analysis())
            continue

        analysis = _analyze_single_paper(abstract, global_keywords)
        analysis['paper_id'] = paper['id']

        # Save to database
        database.save_paper_analysis(session_id, paper['id'], analysis)
        analyses.append(analysis)

    return analyses


def _analyze_single_paper(text, global_keywords=None):
    """Run NLP pipeline on a single paper abstract."""
    doc = nlp(text)

    # Preprocessing results
    tokens = [token.text for token in doc if not token.is_space]
    lemmas = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct and not token.is_space]
    sentences = [sent.text.strip() for sent in doc.sents]

    # POS tagging
    pos_tags = [
        {'token': token.text, 'pos': token.pos_, 'tag': token.tag_}
        for token in doc
        if not token.is_space
    ]

    # Named Entity Recognition
    entities = _extract_entities(doc)

    # Method extraction using domain dictionary
    methods = _extract_from_dictionary(text, RESEARCH_METHODS)

    # Dataset extraction
    datasets = _extract_from_dictionary(text, RESEARCH_DATASETS)

    # Metric extraction
    metrics = _extract_from_dictionary(text, RESEARCH_METRICS)

    # Per-paper keywords from TF-IDF (single document)
    keywords = _extract_paper_keywords(text)

    return {
        'keywords': keywords,
        'entities': entities,
        'methods': methods,
        'datasets': datasets,
        'metrics': metrics,
        'pos_tags': pos_tags[:50],  # Limit stored POS tags to first 50 tokens
        'sentences': sentences,
        'lemmas': lemmas,
        'num_tokens': len(tokens),
        'num_sentences': len(sentences),
    }


def _extract_global_keywords(abstracts):
    """Extract top keywords across all papers using TF-IDF."""
    if not abstracts or all(not a for a in abstracts):
        return []

    # Filter out empty abstracts
    valid_abstracts = [a for a in abstracts if a and len(a.strip()) > 10]
    if not valid_abstracts:
        return []

    vectorizer = TfidfVectorizer(
        max_features=500,
        stop_words='english',
        ngram_range=(1, 3),  # Unigrams, bigrams, trigrams
        min_df=1,
        max_df=0.95,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(valid_abstracts)
        feature_names = vectorizer.get_feature_names_out()

        # Average TF-IDF score across all documents
        avg_scores = tfidf_matrix.mean(axis=0).A1
        top_indices = avg_scores.argsort()[::-1][:TOP_GLOBAL_KEYWORDS]

        keywords = [
            {'term': feature_names[i], 'score': round(float(avg_scores[i]), 4)}
            for i in top_indices
            if avg_scores[i] > 0
        ]
        return keywords
    except ValueError:
        return []


def _extract_paper_keywords(text):
    """Extract keywords from a single paper using TF-IDF."""
    if not text or len(text.strip()) < 10:
        return []

    vectorizer = TfidfVectorizer(
        max_features=200,
        stop_words='english',
        ngram_range=(1, 2),
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        top_indices = scores.argsort()[::-1][:TOP_KEYWORDS]

        keywords = [
            {'term': feature_names[i], 'score': round(float(scores[i]), 4)}
            for i in top_indices
            if scores[i] > 0
        ]
        return keywords
    except ValueError:
        return []


def _extract_entities(doc):
    """Extract named entities using spaCy NER."""
    entities = []
    seen = set()

    for ent in doc.ents:
        # Skip very short or pure number entities
        if len(ent.text.strip()) < 2 or ent.text.strip().isdigit():
            continue

        key = (ent.text.lower().strip(), ent.label_)
        if key not in seen:
            seen.add(key)
            entities.append({
                'text': ent.text.strip(),
                'label': ent.label_,
                'description': spacy.explain(ent.label_) or ent.label_,
            })

    return entities


def _extract_from_dictionary(text, dictionary):
    """
    Extract terms from text using a predefined dictionary.
    Case-insensitive matching.
    """
    text_lower = text.lower()
    found = []
    seen = set()

    for term in dictionary:
        if term.lower() in text_lower and term.lower() not in seen:
            seen.add(term.lower())
            # Find the original case version in text
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            match = pattern.search(text)
            if match:
                found.append(match.group())
            else:
                found.append(term)

    return found


def _empty_analysis():
    """Return empty analysis dict for papers without abstracts."""
    return {
        'keywords': [],
        'entities': [],
        'methods': [],
        'datasets': [],
        'metrics': [],
        'pos_tags': [],
        'sentences': [],
        'lemmas': [],
        'num_tokens': 0,
        'num_sentences': 0,
    }
