from flask import Flask, render_template, request, jsonify, redirect, url_for
import database
from config import SECRET_KEY, DEBUG

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route('/')
def index():
    """Landing page — topic search form + past sessions."""
    sessions = database.get_all_sessions()
    return render_template('index.html', sessions=sessions)


@app.route('/search', methods=['POST'])
def search():
    """Handle topic search — fetch papers and redirect to dashboard."""
    topic = request.form.get('topic', '').strip()
    if not topic:
        return redirect(url_for('index'))

    # Import here to avoid circular imports and slow startup
    from services.paper_search import search_papers

    # Create session
    session_id = database.create_session(topic)

    # Search and save papers
    papers = search_papers(topic)
    for i, paper in enumerate(papers):
        paper_id = database.save_paper(paper)
        database.link_paper_to_session(session_id, paper_id, paper.get('relevance_score', 0.0))

    database.update_session_status(session_id, 'papers_found', len(papers))

    return redirect(url_for('dashboard', session_id=session_id))


@app.route('/dashboard/<int:session_id>')
def dashboard(session_id):
    """Main dashboard page for a research session."""
    session = database.get_session(session_id)
    if not session:
        return redirect(url_for('index'))

    papers = database.get_session_papers(session_id)

    return render_template('dashboard.html', session=session, papers=papers)


@app.route('/api/analyze/<int:session_id>', methods=['POST'])
def analyze(session_id):
    """Run NLP analysis on all papers in a session."""
    try:
        from services.nlp import analyze_papers
        from services.similarity import compute_embeddings, compute_similarity_matrix
        from services.analysis import (
            cluster_papers, extract_trends, find_underrepresented_themes,
            build_methodology_comparison, identify_research_gaps
        )

        session = database.get_session(session_id)
        if not session:
            return jsonify({'status': 'error', 'error': 'Session not found'}), 404

        papers = database.get_session_papers(session_id)
        if not papers:
            return jsonify({'status': 'error', 'error': 'No papers found in session'}), 404

        # Step 1: NLP analysis (keywords, entities, methods)
        analyses = analyze_papers(session_id, papers)

        # Step 2: Embeddings and similarity
        embeddings_data = compute_embeddings(session_id, papers)
        similarity_matrix = compute_similarity_matrix(embeddings_data)

        # Step 3: Clustering
        clusters = cluster_papers(session_id, papers, embeddings_data)

        # Step 4: Trends
        trends = extract_trends(papers, analyses)

        # Step 5: Underrepresented themes
        underrepresented = find_underrepresented_themes(analyses, papers)

        # Step 6: Methodology comparison
        comparison = build_methodology_comparison(papers, analyses)

        # Step 7: Research gaps
        research_gaps = identify_research_gaps(papers, analyses, clusters, similarity_matrix)

        database.update_session_status(session_id, 'analyzed')

        return jsonify({
            'status': 'success',
            'analyses': analyses,
            'similarity_matrix': similarity_matrix,
            'clusters': clusters,
            'trends': trends,
            'underrepresented': underrepresented,
            'comparison': comparison,
            'research_gaps': research_gaps,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/semantic-search/<int:session_id>', methods=['POST'])
def semantic_search(session_id):
    """Semantic search across papers in a session."""
    try:
        from services.similarity import semantic_search as do_search

        query = request.json.get('query', '').strip()
        if not query:
            return jsonify({'error': 'No query provided'}), 400

        papers = database.get_session_papers(session_id)
        results = do_search(session_id, query, papers)

        return jsonify({'results': results})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/report/<int:session_id>')
def report(session_id):
    """Generate and display the research report."""
    session = database.get_session(session_id)
    if not session:
        return redirect(url_for('index'))

    papers = database.get_session_papers(session_id)
    analyses = database.get_all_paper_analyses(session_id)
    topics = database.get_topics(session_id)

    return render_template('report.html',
                           session=session,
                           papers=papers,
                           analyses=analyses,
                           topics=topics)


if __name__ == '__main__':
    database.init_db()
    app.run(debug=DEBUG, use_reloader=False, port=5000)
