// ResearchLens — Frontend JavaScript

async function runAnalysis(sessionId) {
    const btn = document.getElementById('analyze-btn');
    const results = document.getElementById('analysis-results');

    btn.disabled = true;
    btn.textContent = 'Analyzing... (this may take a minute)';
    results.innerHTML = '<div class="loading">Running NLP analysis on all papers...</div>';

    try {
        const response = await fetch(`/api/analyze/${sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.status === 'success') {
            btn.textContent = 'Analysis Complete ✓';
            results.innerHTML = '<div class="loading">Analysis complete! Reload the page to see results.</div>';
            // Reload to show full dashboard
            window.location.reload();
        } else {
            btn.textContent = 'Analysis Failed — Try Again';
            btn.disabled = false;
            results.innerHTML = `<div class="loading">Error: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (err) {
        btn.textContent = 'Analysis Failed — Try Again';
        btn.disabled = false;
        results.innerHTML = `<div class="loading">Error: ${err.message}</div>`;
    }
}
