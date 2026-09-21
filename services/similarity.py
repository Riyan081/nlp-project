import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
import database
from config import EMBEDDING_MODEL

# Lazy-load the model (only when needed, avoids slow startup)
_model = None


def _get_model():
    """Load sentence-transformer model on first use."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading embedding model '{EMBEDDING_MODEL}'... (first time only)")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print("Embedding model loaded.")
    return _model


def compute_embeddings(session_id, papers):
    """
    Generate embeddings for all paper abstracts in a session.
    Returns a list of (paper_id, embedding_vector) tuples.
    """
    model = _get_model()

    abstracts = []
    paper_ids = []

    for paper in papers:
        abstract = paper.get('abstract', '')
        if abstract and len(abstract.strip()) > 10:
            abstracts.append(abstract)
            paper_ids.append(paper['id'])

    if not abstracts:
        return []

    # Generate embeddings in batch
    embeddings = model.encode(abstracts, show_progress_bar=False)

    # Save to database
    result = []
    for i, paper_id in enumerate(paper_ids):
        embedding = embeddings[i]
        # Store as bytes in SQLite
        embedding_bytes = embedding.tobytes()
        database.save_paper_embedding(session_id, paper_id, embedding_bytes)
        result.append((paper_id, embedding))

    return result


def compute_similarity_matrix(embeddings_data):
    """
    Compute cosine similarity matrix between all papers.
    Returns a dict with paper_ids and the similarity matrix as nested lists.
    """
    if not embeddings_data or len(embeddings_data) < 2:
        return {'paper_ids': [], 'matrix': []}

    paper_ids = [item[0] for item in embeddings_data]
    vectors = np.array([item[1] for item in embeddings_data])

    # Compute pairwise cosine similarity
    sim_matrix = sklearn_cosine(vectors)

    # Convert to plain Python types for JSON
    matrix = []
    for row in sim_matrix:
        matrix.append([round(float(val), 4) for val in row])

    return {
        'paper_ids': paper_ids,
        'matrix': matrix,
    }


def semantic_search(session_id, query, papers, top_k=5):
    """
    Search papers by semantic similarity to a natural language query.
    Returns top-k most relevant papers.
    """
    model = _get_model()

    # Get stored embeddings
    stored = database.get_paper_embeddings(session_id)
    if not stored:
        return []

    # Build paper lookup
    paper_lookup = {p['id']: p for p in papers}

    # Decode stored embeddings
    paper_ids = []
    vectors = []
    for paper_id, embedding_bytes in stored:
        if paper_id in paper_lookup:
            # Reconstruct numpy array from bytes
            vector = np.frombuffer(embedding_bytes, dtype=np.float32)
            vectors.append(vector)
            paper_ids.append(paper_id)

    if not vectors:
        return []

    vectors = np.array(vectors)

    # Encode the query
    query_embedding = model.encode([query], show_progress_bar=False)[0]
    query_embedding = query_embedding.reshape(1, -1)

    # Compute similarity
    similarities = sklearn_cosine(query_embedding, vectors)[0]

    # Get top-k results
    top_indices = similarities.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        paper_id = paper_ids[idx]
        paper = paper_lookup.get(paper_id, {})
        results.append({
            'paper_id': paper_id,
            'title': paper.get('title', ''),
            'abstract': paper.get('abstract', '')[:300],
            'year': paper.get('year'),
            'similarity': round(float(similarities[idx]), 4),
        })

    return results
