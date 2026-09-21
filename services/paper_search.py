import requests
import time
import re
from config import SEMANTIC_SCHOLAR_API, PAPERS_TO_FETCH, API_RATE_LIMIT_DELAY


def search_papers(topic, num_papers=None):
    """
    Search Semantic Scholar for papers related to the topic.
    Returns a list of paper dicts with metadata and relevance scores.
    """
    if num_papers is None:
        num_papers = PAPERS_TO_FETCH

    # Fetch more candidates than needed so we can rank and filter
    candidates = _fetch_from_semantic_scholar(topic, limit=num_papers * 3)

    if not candidates:
        return []

    # Deduplicate by title (case-insensitive)
    candidates = _deduplicate(candidates)

    # Rank papers
    candidates = _rank_papers(candidates, topic)

    # Return top N
    return candidates[:num_papers]


def _fetch_from_semantic_scholar(topic, limit=50):
    """Fetch papers from Semantic Scholar Academic Graph API."""
    url = f"{SEMANTIC_SCHOLAR_API}/paper/search"

    params = {
        'query': topic,
        'limit': min(limit, 100),  # API max is 100
        'fields': 'paperId,title,abstract,authors,year,venue,externalIds,url,citationCount,openAccessPdf',
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        papers = []
        for item in data.get('data', []):
            # Skip papers without abstract (we need it for NLP)
            if not item.get('abstract'):
                continue

            # Extract author names
            authors = []
            for author in item.get('authors', []):
                if author.get('name'):
                    authors.append(author['name'])

            # Build DOI
            doi = ''
            external_ids = item.get('externalIds', {})
            if external_ids and external_ids.get('DOI'):
                doi = external_ids['DOI']

            # Build URL — prefer open access PDF, then Semantic Scholar URL
            paper_url = ''
            if item.get('openAccessPdf') and item['openAccessPdf'].get('url'):
                paper_url = item['openAccessPdf']['url']
            elif item.get('url'):
                paper_url = item['url']
            elif doi:
                paper_url = f"https://doi.org/{doi}"

            paper = {
                'external_id': item.get('paperId', ''),
                'title': item.get('title', 'Untitled'),
                'abstract': item.get('abstract', ''),
                'authors': authors,
                'year': item.get('year'),
                'venue': item.get('venue', ''),
                'doi': doi,
                'url': paper_url,
                'citation_count': item.get('citationCount', 0) or 0,
            }
            papers.append(paper)

        time.sleep(API_RATE_LIMIT_DELAY)  # Rate limit
        return papers

    except requests.exceptions.RequestException as e:
        print(f"Error fetching from Semantic Scholar: {e}")
        return []


def _deduplicate(papers):
    """Remove duplicate papers based on normalized title."""
    seen = set()
    unique = []
    for paper in papers:
        # Normalize title for comparison
        normalized = re.sub(r'[^a-z0-9]', '', paper['title'].lower())
        if normalized not in seen:
            seen.add(normalized)
            unique.append(paper)
    return unique


def _rank_papers(papers, topic):
    """
    Rank papers by relevance. Simple scoring based on:
    - Keyword overlap with topic
    - Citation count (log-scaled)
    - Recency (recent papers get a small boost)
    """
    topic_words = set(topic.lower().split())

    for paper in papers:
        score = 0.0

        # Keyword overlap — title and abstract vs topic words
        title_words = set(paper['title'].lower().split())
        abstract_words = set(paper.get('abstract', '').lower().split())

        title_overlap = len(topic_words & title_words) / max(len(topic_words), 1)
        abstract_overlap = len(topic_words & abstract_words) / max(len(topic_words), 1)

        score += title_overlap * 40  # Title match is important
        score += min(abstract_overlap * 20, 20)  # Cap abstract contribution

        # Citation boost (log scale so highly-cited papers don't dominate)
        citations = paper.get('citation_count', 0) or 0
        if citations > 0:
            import math
            score += min(math.log(citations + 1) * 3, 15)

        # Recency boost (small)
        year = paper.get('year')
        if year and year >= 2020:
            score += (year - 2019) * 1.5
        elif year and year >= 2015:
            score += (year - 2014) * 0.5

        # Has abstract boost (we need abstracts for NLP)
        if paper.get('abstract') and len(paper['abstract']) > 100:
            score += 5

        paper['relevance_score'] = round(score, 2)

    # Sort by relevance score descending
    papers.sort(key=lambda p: p['relevance_score'], reverse=True)
    return papers
