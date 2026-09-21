import numpy as np
from collections import Counter, defaultdict
from sklearn.cluster import KMeans
import database
from config import DEFAULT_NUM_CLUSTERS, MAX_CLUSTERS


def cluster_papers(session_id, papers, embeddings_data):
    """
    Cluster papers into research themes using K-Means on embeddings.
    Returns cluster info with labels based on top keywords.
    """
    if not embeddings_data or len(embeddings_data) < 3:
        return []

    paper_ids = [item[0] for item in embeddings_data]
    vectors = np.array([item[1] for item in embeddings_data])

    # Determine number of clusters
    n_clusters = min(DEFAULT_NUM_CLUSTERS, len(paper_ids) - 1)
    n_clusters = max(2, n_clusters)

    # Run K-Means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(vectors)

    # Build paper lookup
    paper_lookup = {p['id']: p for p in papers}

    # Get analyses for keyword-based cluster labeling
    analyses_list = database.get_all_paper_analyses(session_id)
    analysis_lookup = {a['paper_id']: a for a in analyses_list}

    # Organize clusters
    clusters = []
    for cluster_id in range(n_clusters):
        cluster_paper_ids = [
            paper_ids[i] for i in range(len(labels)) if labels[i] == cluster_id
        ]

        # Collect keywords from papers in this cluster
        all_keywords = []
        cluster_methods = []
        for pid in cluster_paper_ids:
            analysis = analysis_lookup.get(pid, {})
            keywords = analysis.get('keywords', [])
            if isinstance(keywords, list):
                for kw in keywords[:10]:
                    if isinstance(kw, dict):
                        all_keywords.append(kw.get('term', ''))
                    else:
                        all_keywords.append(str(kw))
            methods = analysis.get('methods', [])
            if isinstance(methods, list):
                cluster_methods.extend(methods)

        # Top keywords for cluster label
        keyword_counts = Counter(all_keywords)
        top_keywords = [word for word, _ in keyword_counts.most_common(5) if word]

        # Generate cluster label from top keywords
        label = ' / '.join(top_keywords[:3]) if top_keywords else f'Cluster {cluster_id + 1}'

        # Paper details
        cluster_papers_info = []
        for pid in cluster_paper_ids:
            p = paper_lookup.get(pid, {})
            cluster_papers_info.append({
                'paper_id': pid,
                'title': p.get('title', ''),
                'year': p.get('year'),
            })

        clusters.append({
            'id': cluster_id,
            'label': label,
            'keywords': top_keywords,
            'methods': list(set(cluster_methods)),
            'papers': cluster_papers_info,
            'size': len(cluster_paper_ids),
        })

    # Save as topics in database
    topics_for_db = [
        {
            'name': c['label'],
            'frequency': c['size'],
            'paper_ids': [p['paper_id'] for p in c['papers']],
        }
        for c in clusters
    ]
    database.save_topics(session_id, topics_for_db)

    return clusters


def extract_trends(papers, analyses):
    """
    Analyze research trends based on publication years and extracted methods.
    Returns year-based counts and method-year distributions.
    """
    # Papers per year
    year_counts = Counter()
    for paper in papers:
        year = paper.get('year')
        if year:
            year_counts[year] += 1

    # Sort by year
    years_sorted = sorted(year_counts.items())

    # Methods per year
    method_year = defaultdict(lambda: Counter())
    analysis_lookup = {a.get('paper_id'): a for a in analyses if isinstance(a, dict)}

    for paper in papers:
        year = paper.get('year')
        if not year:
            continue
        analysis = analysis_lookup.get(paper['id'], {})
        methods = analysis.get('methods', [])
        if isinstance(methods, list):
            for method in methods:
                method_year[method][year] += 1

    # Build method trends
    method_trends = {}
    for method, year_data in method_year.items():
        method_trends[method] = dict(sorted(year_data.items()))

    # Keywords per year (top keywords)
    keyword_year = defaultdict(lambda: Counter())
    for paper in papers:
        year = paper.get('year')
        if not year:
            continue
        analysis = analysis_lookup.get(paper['id'], {})
        keywords = analysis.get('keywords', [])
        if isinstance(keywords, list):
            for kw in keywords[:5]:
                term = kw.get('term', '') if isinstance(kw, dict) else str(kw)
                if term:
                    keyword_year[term][year] += 1

    # Top 10 keywords by total frequency
    keyword_totals = Counter()
    for term, year_data in keyword_year.items():
        keyword_totals[term] = sum(year_data.values())

    top_keyword_trends = {}
    for term, _ in keyword_totals.most_common(10):
        top_keyword_trends[term] = dict(sorted(keyword_year[term].items()))

    return {
        'papers_per_year': [{'year': y, 'count': c} for y, c in years_sorted],
        'method_trends': method_trends,
        'keyword_trends': top_keyword_trends,
    }


def find_underrepresented_themes(analyses, papers):
    """
    Identify themes that appear less frequently in the selected literature.
    Compares frequency of concepts and methods across all papers.
    """
    total_papers = len(papers)
    if total_papers == 0:
        return []

    # Count method frequency
    method_counts = Counter()
    keyword_counts = Counter()

    for analysis in analyses:
        if not isinstance(analysis, dict):
            continue

        methods = analysis.get('methods', [])
        if isinstance(methods, list):
            for m in methods:
                method_counts[m] += 1

        keywords = analysis.get('keywords', [])
        if isinstance(keywords, list):
            for kw in keywords[:10]:
                term = kw.get('term', '') if isinstance(kw, dict) else str(kw)
                if term and len(term) > 2:
                    keyword_counts[term] += 1

    # Threshold: appears in fewer than 20% of papers
    threshold = max(1, int(total_papers * 0.2))

    underrepresented = []

    # Methods that appear rarely
    for method, count in method_counts.items():
        if count <= threshold:
            underrepresented.append({
                'theme': method,
                'type': 'method',
                'frequency': count,
                'total_papers': total_papers,
                'percentage': round(count / total_papers * 100, 1),
            })

    # Keywords that appear rarely but exist
    for term, count in keyword_counts.items():
        if 1 <= count <= threshold:
            underrepresented.append({
                'theme': term,
                'type': 'keyword',
                'frequency': count,
                'total_papers': total_papers,
                'percentage': round(count / total_papers * 100, 1),
            })

    # Sort by frequency (least frequent first) and limit
    underrepresented.sort(key=lambda x: x['frequency'])
    return underrepresented[:20]


def build_methodology_comparison(papers, analyses):
    """
    Build a comparison table of methods, datasets, and metrics across papers.
    Returns a list of paper comparison records.
    """
    analysis_lookup = {a.get('paper_id'): a for a in analyses if isinstance(a, dict)}

    comparison = []
    for paper in papers:
        analysis = analysis_lookup.get(paper['id'], {})

        methods = analysis.get('methods', [])
        datasets = analysis.get('datasets', [])
        metrics = analysis.get('metrics', [])

        comparison.append({
            'paper_id': paper['id'],
            'title': paper.get('title', ''),
            'year': paper.get('year'),
            'methods': methods if isinstance(methods, list) else [],
            'datasets': datasets if isinstance(datasets, list) else [],
            'metrics': metrics if isinstance(metrics, list) else [],
            'citation_count': paper.get('citation_count', 0),
        })

    return comparison
