import sqlite3
import os
import json
from config import DATABASE_PATH


def get_db():
    """Get a database connection."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()

    # Research sessions — one per topic search
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            num_papers INTEGER DEFAULT 0,
            status TEXT DEFAULT 'searching'
        )
    ''')

    # Papers — unique papers across all sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            title TEXT NOT NULL,
            abstract TEXT,
            authors TEXT,
            year INTEGER,
            venue TEXT,
            doi TEXT,
            url TEXT,
            citation_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Session-paper link with relevance score
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            paper_id INTEGER NOT NULL,
            relevance_score REAL DEFAULT 0.0,
            FOREIGN KEY (session_id) REFERENCES research_sessions(id),
            FOREIGN KEY (paper_id) REFERENCES papers(id),
            UNIQUE(session_id, paper_id)
        )
    ''')

    # Paper analysis results — NLP output per paper per session
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            paper_id INTEGER NOT NULL,
            keywords TEXT,
            entities TEXT,
            methods TEXT,
            datasets TEXT,
            metrics TEXT,
            pos_tags TEXT,
            FOREIGN KEY (session_id) REFERENCES research_sessions(id),
            FOREIGN KEY (paper_id) REFERENCES papers(id),
            UNIQUE(session_id, paper_id)
        )
    ''')

    # Paper embeddings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            paper_id INTEGER NOT NULL,
            embedding BLOB,
            FOREIGN KEY (session_id) REFERENCES research_sessions(id),
            FOREIGN KEY (paper_id) REFERENCES papers(id),
            UNIQUE(session_id, paper_id)
        )
    ''')

    # Topics/themes per session
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            topic_name TEXT NOT NULL,
            frequency INTEGER DEFAULT 0,
            paper_ids TEXT,
            FOREIGN KEY (session_id) REFERENCES research_sessions(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


# --- Helper functions ---

def create_session(topic):
    """Create a new research session and return its ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO research_sessions (topic) VALUES (?)',
        (topic,)
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def update_session_status(session_id, status, num_papers=None):
    """Update session status."""
    conn = get_db()
    if num_papers is not None:
        conn.execute(
            'UPDATE research_sessions SET status=?, num_papers=? WHERE id=?',
            (status, num_papers, session_id)
        )
    else:
        conn.execute(
            'UPDATE research_sessions SET status=? WHERE id=?',
            (status, session_id)
        )
    conn.commit()
    conn.close()


def save_paper(paper_data):
    """Save a paper and return its ID. If it exists, return existing ID."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if paper already exists
    cursor.execute(
        'SELECT id FROM papers WHERE external_id=?',
        (paper_data['external_id'],)
    )
    row = cursor.fetchone()

    if row:
        paper_id = row['id']
    else:
        cursor.execute('''
            INSERT INTO papers (external_id, title, abstract, authors, year, venue, doi, url, citation_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            paper_data['external_id'],
            paper_data['title'],
            paper_data.get('abstract', ''),
            json.dumps(paper_data.get('authors', [])),
            paper_data.get('year'),
            paper_data.get('venue', ''),
            paper_data.get('doi', ''),
            paper_data.get('url', ''),
            paper_data.get('citation_count', 0),
        ))
        paper_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return paper_id


def link_paper_to_session(session_id, paper_id, relevance_score=0.0):
    """Link a paper to a session with a relevance score."""
    conn = get_db()
    try:
        conn.execute(
            'INSERT OR IGNORE INTO session_papers (session_id, paper_id, relevance_score) VALUES (?, ?, ?)',
            (session_id, paper_id, relevance_score)
        )
        conn.commit()
    finally:
        conn.close()


def get_session(session_id):
    """Get session details."""
    conn = get_db()
    session = conn.execute(
        'SELECT * FROM research_sessions WHERE id=?', (session_id,)
    ).fetchone()
    conn.close()
    return dict(session) if session else None


def get_session_papers(session_id):
    """Get all papers for a session, ordered by relevance."""
    conn = get_db()
    papers = conn.execute('''
        SELECT p.*, sp.relevance_score
        FROM papers p
        JOIN session_papers sp ON p.id = sp.paper_id
        WHERE sp.session_id = ?
        ORDER BY sp.relevance_score DESC
    ''', (session_id,)).fetchall()
    conn.close()
    return [dict(p) for p in papers]


def get_all_sessions():
    """Get all research sessions, newest first."""
    conn = get_db()
    sessions = conn.execute(
        'SELECT * FROM research_sessions ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    return [dict(s) for s in sessions]


def save_paper_analysis(session_id, paper_id, analysis_data):
    """Save NLP analysis results for a paper."""
    conn = get_db()
    conn.execute('''
        INSERT OR REPLACE INTO paper_analysis
        (session_id, paper_id, keywords, entities, methods, datasets, metrics, pos_tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id, paper_id,
        json.dumps(analysis_data.get('keywords', [])),
        json.dumps(analysis_data.get('entities', [])),
        json.dumps(analysis_data.get('methods', [])),
        json.dumps(analysis_data.get('datasets', [])),
        json.dumps(analysis_data.get('metrics', [])),
        json.dumps(analysis_data.get('pos_tags', [])),
    ))
    conn.commit()
    conn.close()


def get_paper_analysis(session_id, paper_id):
    """Get analysis results for a paper in a session."""
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM paper_analysis WHERE session_id=? AND paper_id=?',
        (session_id, paper_id)
    ).fetchone()
    conn.close()
    if row:
        result = dict(row)
        for field in ['keywords', 'entities', 'methods', 'datasets', 'metrics', 'pos_tags']:
            if result.get(field):
                result[field] = json.loads(result[field])
        return result
    return None


def get_all_paper_analyses(session_id):
    """Get analysis results for all papers in a session."""
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM paper_analysis WHERE session_id=?',
        (session_id,)
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        result = dict(row)
        for field in ['keywords', 'entities', 'methods', 'datasets', 'metrics', 'pos_tags']:
            if result.get(field):
                result[field] = json.loads(result[field])
        results.append(result)
    return results


def save_paper_embedding(session_id, paper_id, embedding_bytes):
    """Save embedding vector for a paper."""
    conn = get_db()
    conn.execute(
        'INSERT OR REPLACE INTO paper_embeddings (session_id, paper_id, embedding) VALUES (?, ?, ?)',
        (session_id, paper_id, embedding_bytes)
    )
    conn.commit()
    conn.close()


def get_paper_embeddings(session_id):
    """Get all embeddings for a session."""
    conn = get_db()
    rows = conn.execute(
        'SELECT paper_id, embedding FROM paper_embeddings WHERE session_id=?',
        (session_id,)
    ).fetchall()
    conn.close()
    return [(row['paper_id'], row['embedding']) for row in rows]


def save_topics(session_id, topics_list):
    """Save extracted topics/themes for a session."""
    conn = get_db()
    # Clear old topics
    conn.execute('DELETE FROM topics WHERE session_id=?', (session_id,))
    for topic in topics_list:
        conn.execute(
            'INSERT INTO topics (session_id, topic_name, frequency, paper_ids) VALUES (?, ?, ?, ?)',
            (session_id, topic['name'], topic['frequency'], json.dumps(topic.get('paper_ids', [])))
        )
    conn.commit()
    conn.close()


def get_topics(session_id):
    """Get topics for a session."""
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM topics WHERE session_id=? ORDER BY frequency DESC',
        (session_id,)
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        r = dict(row)
        if r.get('paper_ids'):
            r['paper_ids'] = json.loads(r['paper_ids'])
        results.append(r)
    return results
