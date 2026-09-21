// ===== ResearchLens — Frontend JavaScript =====

// --- Tab Navigation ---
document.addEventListener('DOMContentLoaded', function() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            const tabId = 'tab-' + btn.getAttribute('data-tab');
            const target = document.getElementById(tabId);
            if (target) target.classList.add('active');
        });
    });
});


// --- Run NLP Analysis ---
async function runAnalysis(sessionId) {
    const btn = document.getElementById('analyzeBtn');
    const progress = document.getElementById('analysisProgress');
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');

    btn.disabled = true;
    btn.style.display = 'none';
    progress.style.display = 'block';

    // Simulate progress steps
    const steps = [
        { pct: 10, msg: 'Extracting keywords with TF-IDF...' },
        { pct: 25, msg: 'Running Named Entity Recognition...' },
        { pct: 40, msg: 'Extracting methods & datasets...' },
        { pct: 55, msg: 'Computing sentence embeddings...' },
        { pct: 70, msg: 'Calculating similarity matrix...' },
        { pct: 80, msg: 'Clustering papers with K-Means...' },
        { pct: 90, msg: 'Analyzing trends...' },
    ];

    let stepIdx = 0;
    const progressInterval = setInterval(() => {
        if (stepIdx < steps.length) {
            fill.style.width = steps[stepIdx].pct + '%';
            text.textContent = steps[stepIdx].msg;
            stepIdx++;
        }
    }, 2000);

    try {
        const response = await fetch(`/api/analyze/${sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        clearInterval(progressInterval);
        const data = await response.json();

        if (data.status === 'success') {
            fill.style.width = '100%';
            text.textContent = 'Analysis complete! Loading results...';

            setTimeout(() => {
                renderResults(data);
                document.getElementById('analyzeSection').style.display = 'none';
            }, 500);
        } else {
            text.textContent = 'Analysis failed: ' + (data.error || 'Unknown error');
            fill.style.background = '#ef4444';
        }
    } catch (err) {
        clearInterval(progressInterval);
        text.textContent = 'Error: ' + err.message;
        fill.style.background = '#ef4444';
    }
}


// --- Render All Analysis Results ---
function renderResults(data) {
    renderKeywords(data.analyses);
    renderClusters(data.clusters);
    renderComparison(data.comparison);
    renderTrends(data.trends);
    renderSimilarityHeatmap(data.similarity_matrix);
    renderUnderrepresented(data.underrepresented);
    renderResearchGaps(data.research_gaps);
}


// --- Keywords & Entities ---
function renderKeywords(analyses) {
    const container = document.getElementById('keywordsContent');
    if (!analyses || analyses.length === 0) {
        container.innerHTML = '<p class="placeholder-text">No analysis data available.</p>';
        return;
    }

    // Collect all keywords, methods, entities
    const allKeywords = [];
    const allMethods = new Set();
    const allEntities = [];
    const allDatasets = new Set();
    const allMetrics = new Set();

    analyses.forEach(a => {
        if (a.keywords) {
            a.keywords.forEach(kw => {
                if (typeof kw === 'object') allKeywords.push(kw);
            });
        }
        if (a.methods) a.methods.forEach(m => allMethods.add(m));
        if (a.entities) a.entities.forEach(e => allEntities.push(e));
        if (a.datasets) a.datasets.forEach(d => allDatasets.add(d));
        if (a.metrics) a.metrics.forEach(m => allMetrics.add(m));
    });

    // Top keywords by average score
    const kwMap = {};
    allKeywords.forEach(kw => {
        const term = kw.term || '';
        if (!kwMap[term]) kwMap[term] = { term, totalScore: 0, count: 0 };
        kwMap[term].totalScore += kw.score || 0;
        kwMap[term].count += 1;
    });
    const topKW = Object.values(kwMap)
        .map(k => ({ ...k, avgScore: k.totalScore / k.count }))
        .sort((a, b) => b.avgScore - a.avgScore)
        .slice(0, 30);

    // Unique entities
    const uniqueEntities = [];
    const seenEnt = new Set();
    allEntities.forEach(e => {
        const key = e.text + '|' + e.label;
        if (!seenEnt.has(key)) {
            seenEnt.add(key);
            uniqueEntities.push(e);
        }
    });

    let html = '<div class="keywords-grid">';

    // Left: keyword cloud + methods
    html += '<div>';
    html += '<h3 style="color:#fff;margin-bottom:0.8rem;">Top Keywords (TF-IDF)</h3>';
    html += '<div class="keyword-cloud">';
    topKW.forEach(kw => {
        html += `<span class="keyword-tag">${kw.term}</span>`;
    });
    html += '</div>';

    if (allMethods.size > 0) {
        html += '<h3 style="color:#fff;margin:1.2rem 0 0.8rem;">Methods Detected</h3>';
        html += '<div class="keyword-cloud">';
        allMethods.forEach(m => { html += `<span class="keyword-tag method">${m}</span>`; });
        html += '</div>';
    }

    if (allDatasets.size > 0) {
        html += '<h3 style="color:#fff;margin:1.2rem 0 0.8rem;">Datasets</h3>';
        html += '<div class="keyword-cloud">';
        allDatasets.forEach(d => { html += `<span class="keyword-tag dataset">${d}</span>`; });
        html += '</div>';
    }

    if (allMetrics.size > 0) {
        html += '<h3 style="color:#fff;margin:1.2rem 0 0.8rem;">Metrics</h3>';
        html += '<div class="keyword-cloud">';
        allMetrics.forEach(m => { html += `<span class="keyword-tag metric">${m}</span>`; });
        html += '</div>';
    }
    html += '</div>';

    // Right: entities table
    html += '<div>';
    html += '<h3 style="color:#fff;margin-bottom:0.8rem;">Named Entities (NER)</h3>';
    if (uniqueEntities.length > 0) {
        html += '<table class="entity-table"><thead><tr><th>Entity</th><th>Type</th></tr></thead><tbody>';
        uniqueEntities.slice(0, 30).forEach(e => {
            html += `<tr><td>${e.text}</td><td><span class="keyword-tag entity">${e.label}</span></td></tr>`;
        });
        html += '</tbody></table>';
    } else {
        html += '<p class="placeholder-text">No entities found.</p>';
    }
    html += '</div>';

    html += '</div>';
    container.innerHTML = html;
}


// --- Clusters ---
function renderClusters(clusters) {
    const container = document.getElementById('clustersContent');
    if (!clusters || clusters.length === 0) {
        container.innerHTML = '<p class="placeholder-text">No clusters available.</p>';
        return;
    }

    const colors = ['#6366f1', '#34d399', '#fbbf24', '#f472b6', '#38bdf8'];
    let html = '';

    clusters.forEach((cluster, i) => {
        const color = colors[i % colors.length];
        html += `<div class="cluster-card" style="border-left: 3px solid ${color};">`;
        html += `<div class="cluster-header">`;
        html += `<span class="cluster-label" style="color:${color};">Cluster ${i + 1}: ${cluster.label}</span>`;
        html += `<span class="cluster-size">${cluster.size} papers</span>`;
        html += `</div>`;

        if (cluster.methods && cluster.methods.length > 0) {
            html += '<div class="keyword-cloud" style="margin-bottom:0.5rem;">';
            cluster.methods.forEach(m => { html += `<span class="keyword-tag method">${m}</span>`; });
            html += '</div>';
        }

        html += '<ul class="cluster-papers">';
        cluster.papers.forEach(p => {
            html += `<li>${p.title} (${p.year || 'N/A'})</li>`;
        });
        html += '</ul></div>';
    });

    container.innerHTML = html;
}


// --- Methodology Comparison Table ---
function renderComparison(comparison) {
    const container = document.getElementById('comparisonContent');
    if (!comparison || comparison.length === 0) {
        container.innerHTML = '<p class="placeholder-text">No comparison data available.</p>';
        return;
    }

    let html = '<div class="comparison-wrapper"><table class="comparison-table">';
    html += '<thead><tr><th>Paper</th><th>Year</th><th>Methods</th><th>Datasets</th><th>Metrics</th><th>Citations</th></tr></thead>';
    html += '<tbody>';

    comparison.forEach(row => {
        const title = row.title.length > 60 ? row.title.substring(0, 60) + '...' : row.title;
        html += '<tr>';
        html += `<td>${title}</td>`;
        html += `<td>${row.year || 'N/A'}</td>`;
        html += `<td>${(row.methods || []).map(m => `<span class="keyword-tag method">${m}</span>`).join(' ') || '—'}</td>`;
        html += `<td>${(row.datasets || []).map(d => `<span class="keyword-tag dataset">${d}</span>`).join(' ') || '—'}</td>`;
        html += `<td>${(row.metrics || []).map(m => `<span class="keyword-tag metric">${m}</span>`).join(' ') || '—'}</td>`;
        html += `<td>${row.citation_count || 0}</td>`;
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    container.innerHTML = html;
}


// --- Trend Charts ---
function renderTrends(trends) {
    const container = document.getElementById('trendsContent');
    if (!trends) {
        container.innerHTML = '<p class="placeholder-text">No trend data available.</p>';
        return;
    }

    let html = '<div class="charts-grid">';

    // Papers per year
    html += '<div class="chart-card"><h3>Papers per Year</h3><canvas id="papersYearChart"></canvas></div>';

    // Methods distribution
    html += '<div class="chart-card"><h3>Methods Distribution</h3><canvas id="methodsChart"></canvas></div>';

    // Method trends over time
    if (trends.method_trends && Object.keys(trends.method_trends).length > 0) {
        html += '<div class="chart-card full-width"><h3>Method Trends Over Time</h3><canvas id="methodTrendsChart"></canvas></div>';
    }

    // Keyword trends
    if (trends.keyword_trends && Object.keys(trends.keyword_trends).length > 0) {
        html += '<div class="chart-card full-width"><h3>Keyword Trends Over Time</h3><canvas id="keywordTrendsChart"></canvas></div>';
    }

    html += '</div>';
    container.innerHTML = html;

    // Render charts after DOM update
    setTimeout(() => {
        renderPapersPerYearChart(trends.papers_per_year);
        renderMethodsChart(trends.method_trends);
        if (trends.method_trends && Object.keys(trends.method_trends).length > 0) {
            renderMethodTrendsChart(trends.method_trends);
        }
        if (trends.keyword_trends && Object.keys(trends.keyword_trends).length > 0) {
            renderKeywordTrendsChart(trends.keyword_trends);
        }
    }, 100);
}


function renderPapersPerYearChart(data) {
    const ctx = document.getElementById('papersYearChart');
    if (!ctx || !data || data.length === 0) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.year),
            datasets: [{
                label: 'Papers',
                data: data.map(d => d.count),
                backgroundColor: 'rgba(99, 102, 241, 0.6)',
                borderColor: '#6366f1',
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1, color: '#888' }, grid: { color: '#1e1e30' } },
                x: { ticks: { color: '#888' }, grid: { display: false } }
            }
        }
    });
}


function renderMethodsChart(methodTrends) {
    const ctx = document.getElementById('methodsChart');
    if (!ctx || !methodTrends) return;

    const methods = Object.keys(methodTrends);
    const counts = methods.map(m => Object.values(methodTrends[m]).reduce((a, b) => a + b, 0));

    const colors = [
        '#6366f1', '#34d399', '#fbbf24', '#f472b6', '#38bdf8',
        '#a78bfa', '#fb923c', '#4ade80', '#f87171', '#22d3ee'
    ];

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: methods,
            datasets: [{
                data: counts,
                backgroundColor: colors.slice(0, methods.length),
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#ccc', padding: 12, font: { size: 11 } }
                }
            }
        }
    });
}


function renderMethodTrendsChart(methodTrends) {
    const ctx = document.getElementById('methodTrendsChart');
    if (!ctx) return;

    const allYears = new Set();
    Object.values(methodTrends).forEach(yd => Object.keys(yd).forEach(y => allYears.add(parseInt(y))));
    const years = Array.from(allYears).sort();

    const colors = [
        '#6366f1', '#34d399', '#fbbf24', '#f472b6', '#38bdf8',
        '#a78bfa', '#fb923c', '#4ade80', '#f87171', '#22d3ee'
    ];

    const datasets = Object.keys(methodTrends).map((method, i) => ({
        label: method,
        data: years.map(y => methodTrends[method][y] || 0),
        borderColor: colors[i % colors.length],
        backgroundColor: colors[i % colors.length] + '22',
        fill: false,
        tension: 0.3,
        pointRadius: 4,
    }));

    new Chart(ctx, {
        type: 'line',
        data: { labels: years, datasets },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#ccc', font: { size: 11 } } } },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1, color: '#888' }, grid: { color: '#1e1e30' } },
                x: { ticks: { color: '#888' }, grid: { display: false } }
            }
        }
    });
}


function renderKeywordTrendsChart(keywordTrends) {
    const ctx = document.getElementById('keywordTrendsChart');
    if (!ctx) return;

    const allYears = new Set();
    Object.values(keywordTrends).forEach(yd => Object.keys(yd).forEach(y => allYears.add(parseInt(y))));
    const years = Array.from(allYears).sort();

    const colors = [
        '#818cf8', '#6ee7b7', '#fcd34d', '#f9a8d4', '#7dd3fc',
        '#c4b5fd', '#fdba74', '#86efac', '#fca5a5', '#67e8f9'
    ];

    // Only show top 5 keywords
    const topKeywords = Object.entries(keywordTrends)
        .map(([term, yd]) => ({ term, total: Object.values(yd).reduce((a, b) => a + b, 0) }))
        .sort((a, b) => b.total - a.total)
        .slice(0, 5)
        .map(k => k.term);

    const datasets = topKeywords.map((kw, i) => ({
        label: kw,
        data: years.map(y => keywordTrends[kw][y] || 0),
        borderColor: colors[i % colors.length],
        fill: false,
        tension: 0.3,
        pointRadius: 4,
    }));

    new Chart(ctx, {
        type: 'line',
        data: { labels: years, datasets },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#ccc', font: { size: 11 } } } },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1, color: '#888' }, grid: { color: '#1e1e30' } },
                x: { ticks: { color: '#888' }, grid: { display: false } }
            }
        }
    });
}


// --- Similarity Heatmap ---
function renderSimilarityHeatmap(simData) {
    if (!simData || !simData.matrix || simData.matrix.length < 2) return;

    const section = document.getElementById('similaritySection');
    section.style.display = 'block';

    const canvas = document.getElementById('similarityCanvas');
    const ctx = canvas.getContext('2d');
    const n = simData.matrix.length;
    const cellSize = Math.min(50, Math.floor(600 / n));
    const padding = 10;

    canvas.width = n * cellSize + padding * 2;
    canvas.height = n * cellSize + padding * 2;

    for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
            const val = simData.matrix[i][j];
            const intensity = Math.floor(val * 255);
            ctx.fillStyle = `rgb(${Math.floor(99 * val)}, ${Math.floor(102 * val)}, ${Math.floor(241 * val)})`;
            ctx.fillRect(padding + j * cellSize, padding + i * cellSize, cellSize - 1, cellSize - 1);

            // Show value
            if (cellSize > 25) {
                ctx.fillStyle = val > 0.5 ? '#fff' : '#888';
                ctx.font = '10px Inter';
                ctx.textAlign = 'center';
                ctx.fillText(val.toFixed(2), padding + j * cellSize + cellSize / 2, padding + i * cellSize + cellSize / 2 + 3);
            }
        }
    }

    // Paper labels
    ctx.fillStyle = '#9ca3af';
    ctx.font = '9px Inter';
    ctx.textAlign = 'right';
    for (let i = 0; i < n; i++) {
        ctx.fillText(`P${i + 1}`, padding - 2, padding + i * cellSize + cellSize / 2 + 3);
    }
    ctx.textAlign = 'center';
    for (let j = 0; j < n; j++) {
        ctx.fillText(`P${j + 1}`, padding + j * cellSize + cellSize / 2, padding + n * cellSize + 12);
    }
}


// --- Underrepresented Themes ---
function renderUnderrepresented(themes) {
    if (!themes || themes.length === 0) return;

    const section = document.getElementById('underrepresentedSection');
    section.style.display = 'block';

    const container = document.getElementById('underrepresentedContent');
    let html = '';

    themes.slice(0, 15).forEach(t => {
        const pct = t.percentage;
        html += `<div class="theme-bar">`;
        html += `<span class="theme-name">${t.theme}</span>`;
        html += `<div class="theme-bar-track"><div class="theme-bar-fill" style="width:${Math.max(pct, 3)}%;"></div></div>`;
        html += `<span class="theme-bar-label">${t.frequency}/${t.total_papers} papers (${pct}%)</span>`;
        html += `</div>`;
    });

    container.innerHTML = html;
}


// --- Semantic Search ---
async function semanticSearch(sessionId) {
    const input = document.getElementById('semanticQuery');
    const results = document.getElementById('searchResults');
    const query = input.value.trim();

    if (!query) return;

    results.innerHTML = '<p class="placeholder-text">Searching...</p>';

    try {
        const response = await fetch(`/api/semantic-search/${sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();

        if (data.results && data.results.length > 0) {
            let html = '';
            data.results.forEach(r => {
                html += `<div class="search-result">`;
                html += `<h4>${r.title}</h4>`;
                html += `<span class="similarity-score">Similarity: ${(r.similarity * 100).toFixed(1)}%</span>`;
                html += `<span style="color:#9ca3af;font-size:0.8rem;margin-left:0.5rem;">${r.year || ''}</span>`;
                html += `<p>${r.abstract}...</p>`;
                html += `</div>`;
            });
            results.innerHTML = html;
        } else {
            results.innerHTML = '<p class="placeholder-text">No results found.</p>';
        }
    } catch (err) {
        results.innerHTML = `<p class="placeholder-text">Error: ${err.message}</p>`;
    }
}


// --- Research Gaps ---
function renderResearchGaps(gapsData) {
    const container = document.getElementById('gapsContent');
    if (!gapsData || !gapsData.gaps || gapsData.gaps.length === 0) {
        container.innerHTML = '<p class="placeholder-text">No significant research gaps identified.</p>';
        return;
    }

    const severityColors = { high: '#ef4444', medium: '#f59e0b', low: '#6366f1' };
    const severityIcons = { high: '🔴', medium: '🟡', low: '🔵' };

    let html = '';

    // Summary header
    html += '<div class="gap-summary" style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:1.2rem;margin-bottom:1.5rem;">';
    html += `<p style="color:#a5b4fc;font-size:0.95rem;margin-bottom:0.3rem;">📊 ${gapsData.summary}</p>`;
    html += `<p style="color:#6b7280;font-size:0.82rem;">${gapsData.total_methods} unique methods detected across ${gapsData.total_papers} papers</p>`;
    html += '</div>';

    // Gap cards
    gapsData.gaps.forEach((gap, idx) => {
        const color = severityColors[gap.severity] || '#6366f1';
        const icon = severityIcons[gap.severity] || '🔵';

        html += `<div class="gap-card" style="background:rgba(15,15,30,0.6);border:1px solid #1e1e30;border-left:3px solid ${color};border-radius:10px;padding:1.2rem;margin-bottom:1rem;">`;
        html += `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem;">`;
        html += `<h3 style="color:#fff;font-size:1rem;font-weight:600;">${icon} ${gap.title}</h3>`;
        html += `<span style="background:${color}22;color:${color};padding:0.2rem 0.7rem;border-radius:12px;font-size:0.75rem;font-weight:600;text-transform:uppercase;">${gap.severity}</span>`;
        html += `</div>`;
        html += `<p style="color:#9ca3af;font-size:0.88rem;margin-bottom:0.8rem;">${gap.description}</p>`;

        if (gap.items && gap.items.length > 0) {
            html += '<div class="keyword-cloud" style="gap:0.4rem;">';
            gap.items.forEach(item => {
                html += `<span class="keyword-tag" style="border-left:2px solid ${color};">${item}</span>`;
            });
            html += '</div>';
        }

        html += '</div>';
    });

    container.innerHTML = html;
}
