import requests
import time
import re
import math
from config import SEMANTIC_SCHOLAR_API, PAPERS_TO_FETCH, API_RATE_LIMIT_DELAY


def search_papers(topic, num_papers=None):
    """
    Search for papers related to the topic.
    Tries Semantic Scholar first, falls back to OpenAlex if rate-limited.
    Returns a list of paper dicts with metadata and relevance scores.
    """
    if num_papers is None:
        num_papers = PAPERS_TO_FETCH

    # Try Semantic Scholar first
    candidates = _fetch_from_semantic_scholar(topic, limit=num_papers * 2)

    # Fallback to OpenAlex if Semantic Scholar fails
    if not candidates:
        print("Semantic Scholar failed. Trying OpenAlex...")
        candidates = _fetch_from_openalex(topic, limit=num_papers * 2)

    if not candidates:
        return []

    # Deduplicate by title (case-insensitive)
    candidates = _deduplicate(candidates)

    # Rank papers
    candidates = _rank_papers(candidates, topic)

    # Return top N
    return candidates[:num_papers]


def _fetch_from_semantic_scholar(topic, limit=30):
    """Fetch papers from Semantic Scholar Academic Graph API with retry."""
    url = f"{SEMANTIC_SCHOLAR_API}/paper/search"

    params = {
        'query': topic,
        'limit': min(limit, 50),
        'fields': 'paperId,title,abstract,authors,year,venue,externalIds,url,citationCount,openAccessPdf',
    }

    headers = {
        'User-Agent': 'ResearchLens/1.0 (Academic Research Tool)',
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            time.sleep(API_RATE_LIMIT_DELAY * (attempt + 1))
            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code == 429:
                wait_time = (attempt + 1) * 5
                print(f"Semantic Scholar rate limited (429). Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get('data', []):
                if not item.get('abstract'):
                    continue

                authors = [a['name'] for a in item.get('authors', []) if a.get('name')]

                doi = ''
                external_ids = item.get('externalIds', {})
                if external_ids and external_ids.get('DOI'):
                    doi = external_ids['DOI']

                paper_url = ''
                if item.get('openAccessPdf') and item['openAccessPdf'].get('url'):
                    paper_url = item['openAccessPdf']['url']
                elif item.get('url'):
                    paper_url = item['url']
                elif doi:
                    paper_url = f"https://doi.org/{doi}"

                papers.append({
                    'external_id': item.get('paperId', ''),
                    'title': item.get('title', 'Untitled'),
                    'abstract': item.get('abstract', ''),
                    'authors': authors,
                    'year': item.get('year'),
                    'venue': item.get('venue', ''),
                    'doi': doi,
                    'url': paper_url,
                    'citation_count': item.get('citationCount', 0) or 0,
                })

            print(f"Fetched {len(papers)} papers from Semantic Scholar.")
            return papers

        except requests.exceptions.RequestException as e:
            print(f"Semantic Scholar error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return []

    print("Semantic Scholar: all retries exhausted.")
    return []


def _fetch_from_openalex(topic, limit=30):
    """
    Fetch papers from OpenAlex API (free, no rate limits, no API key needed).
    https://docs.openalex.org/
    """
    url = "https://api.openalex.org/works"

    params = {
        'search': topic,
        'per_page': min(limit, 50),
        'filter': 'has_abstract:true',
        'sort': 'relevance_score:desc',
        'mailto': 'researchlens@example.com',  # Polite pool for better rate limits
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        papers = []
        for item in data.get('results', []):
            # OpenAlex stores abstract as inverted index — reconstruct it
            abstract = _reconstruct_openalex_abstract(item.get('abstract_inverted_index', {}))
            if not abstract or len(abstract) < 30:
                continue

            # Extract author names
            authors = []
            for authorship in item.get('authorships', []):
                author = authorship.get('author', {})
                name = author.get('display_name', '')
                if name:
                    authors.append(name)

            # Get DOI
            doi = ''
            doi_url = item.get('doi', '')
            if doi_url:
                doi = doi_url.replace('https://doi.org/', '')

            # Get year
            year = item.get('publication_year')

            # Get venue
            venue = ''
            primary_location = item.get('primary_location', {})
            if primary_location:
                source = primary_location.get('source', {})
                if source:
                    venue = source.get('display_name', '')

            # Build URL
            paper_url = ''
            if primary_location and primary_location.get('landing_page_url'):
                paper_url = primary_location['landing_page_url']
            elif doi:
                paper_url = f"https://doi.org/{doi}"

            # Citation count
            citation_count = item.get('cited_by_count', 0) or 0

            # External ID from OpenAlex
            openalex_id = item.get('id', '').replace('https://openalex.org/', '')

            papers.append({
                'external_id': openalex_id,
                'title': item.get('title', 'Untitled') or 'Untitled',
                'abstract': abstract,
                'authors': authors,
                'year': year,
                'venue': venue,
                'doi': doi,
                'url': paper_url,
                'citation_count': citation_count,
            })

        print(f"Fetched {len(papers)} papers from OpenAlex.")
        return papers

    except requests.exceptions.RequestException as e:
        print(f"OpenAlex error: {e}")
        return []


def _reconstruct_openalex_abstract(inverted_index):
    """
    OpenAlex stores abstracts as inverted indexes like:
    {"word1": [0, 5], "word2": [1, 3], ...}
    Reconstruct into a regular string.
    """
    if not inverted_index:
        return ''

    try:
        # Build position -> word mapping
        positions = {}
        for word, pos_list in inverted_index.items():
            for pos in pos_list:
                positions[pos] = word

        # Sort by position and join
        max_pos = max(positions.keys()) if positions else 0
        words = [positions.get(i, '') for i in range(max_pos + 1)]
        return ' '.join(words)
    except (ValueError, TypeError):
        return ''


def _deduplicate(papers):
    """Remove duplicate papers based on normalized title."""
    seen = set()
    unique = []
    for paper in papers:
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

        title_words = set(paper['title'].lower().split())
        abstract_words = set(paper.get('abstract', '').lower().split())

        title_overlap = len(topic_words & title_words) / max(len(topic_words), 1)
        abstract_overlap = len(topic_words & abstract_words) / max(len(topic_words), 1)

        score += title_overlap * 40
        score += min(abstract_overlap * 20, 20)

        citations = paper.get('citation_count', 0) or 0
        if citations > 0:
            score += min(math.log(citations + 1) * 3, 15)

        year = paper.get('year')
        if year and year >= 2020:
            score += (year - 2019) * 1.5
        elif year and year >= 2015:
            score += (year - 2014) * 0.5

        if paper.get('abstract') and len(paper['abstract']) > 100:
            score += 5

        paper['relevance_score'] = round(score, 2)

    papers.sort(key=lambda p: p['relevance_score'], reverse=True)
    return papers
