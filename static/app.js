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
    renderTrends(data.trends);
    renderResearchResults(data.analyses, data.research_gaps, data.trends);
}


// --- Keywords & Entities ---
function renderKeywords(analyses) {
    const container = document.getElementById('keywordsContent');
    if (!analyses || analyses.length === 0) {
        container.innerHTML = '<p class="placeholder-text">No analysis data available.</p>';
        return;
    }

    // Collect all keywords, methods
    const allKeywords = [];
    const allMethods = new Set();
    const allDatasets = new Set();
    const allMetrics = new Set();

    analyses.forEach(a => {
        if (a.keywords) {
            a.keywords.forEach(kw => {
                if (typeof kw === 'object') allKeywords.push(kw);
            });
        }
        if (a.methods) a.methods.forEach(m => allMethods.add(m));

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


    let html = '<div class="keywords-section">';

    // Keywords, methods, datasets, metrics
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

    // Papers per year (simple bar chart)
    html += '<div class="chart-card"><h3>Papers per Year</h3><canvas id="papersYearChart"></canvas></div>';

    // Methods distribution (simple donut chart)
    html += '<div class="chart-card"><h3>Methods Distribution</h3><canvas id="methodsChart"></canvas></div>';

    html += '</div>';
    container.innerHTML = html;

    // Render charts after DOM update
    setTimeout(() => {
        renderPapersPerYearChart(trends.papers_per_year);
        renderMethodsChart(trends.method_trends);
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


// --- Results: Most Common Research Areas + Future Work ---
function renderResearchResults(analyses, gapsData, trends) {
    const container = document.getElementById('gapsContent');
    if (!analyses || analyses.length === 0) {
        container.innerHTML = '<p class="placeholder-text">No analysis data available.</p>';
        return;
    }

    let html = '';

    // ========== SECTION 1: Most Common Research Areas ==========
    html += '<div class="results-section" style="margin-bottom:2.5rem;">';
    html += '<h2 style="color:#fff;font-size:1.3rem;font-weight:600;margin-bottom:0.5rem;padding-bottom:0.5rem;border-bottom:1px solid #1e1e30;"><span style="color:#6366f1;">1.</span> Most Common Research Areas</h2>';
    html += '<p style="color:#9ca3af;font-size:0.88rem;margin-bottom:1.2rem;">Based on analysis of all papers, the following are the most frequently researched topics, methods, and themes in this field.</p>';

    // --- Top Methods (most popular) ---
    const methodCounts = {};
    analyses.forEach(a => {
        if (a.methods && Array.isArray(a.methods)) {
            a.methods.forEach(m => {
                methodCounts[m] = (methodCounts[m] || 0) + 1;
            });
        }
    });

    const totalPapers = analyses.length;
    const sortedMethods = Object.entries(methodCounts)
        .sort((a, b) => b[1] - a[1]);

    if (sortedMethods.length > 0) {
        html += '<div style="background:#13131f;border:1px solid #1e1e30;border-radius:10px;padding:1.5rem;margin-bottom:1rem;">';
        html += '<h3 style="color:#6ee7b7;font-size:1rem;margin-bottom:0.8rem;">🔬 Most Used Methods & Techniques</h3>';
        html += '<p style="color:#777;font-size:0.82rem;margin-bottom:1rem;">Methods ranked by how many papers use them:</p>';

        sortedMethods.forEach(([method, count]) => {
            const pct = Math.round(count / totalPapers * 100);
            const barColor = pct >= 50 ? '#34d399' : pct >= 25 ? '#6366f1' : '#9ca3af';
            html += `<div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.6rem;">`;
            html += `<span style="min-width:200px;font-size:0.88rem;color:#e0e0e0;text-align:right;">${method}</span>`;
            html += `<div style="flex:1;height:22px;background:#1e1e30;border-radius:4px;overflow:hidden;">`;
            html += `<div style="height:100%;width:${Math.max(pct, 5)}%;background:${barColor};border-radius:4px;transition:width 0.5s;"></div>`;
            html += `</div>`;
            html += `<span style="font-size:0.78rem;color:#9ca3af;min-width:90px;">${count}/${totalPapers} papers (${pct}%)</span>`;
            html += `</div>`;
        });

        html += '</div>';
    }

    // --- Top Keywords (most researched topics) ---
    const keywordCounts = {};
    analyses.forEach(a => {
        if (a.keywords && Array.isArray(a.keywords)) {
            a.keywords.slice(0, 5).forEach(kw => {
                const term = (typeof kw === 'object') ? kw.term : String(kw);
                if (term && term.length > 2) {
                    keywordCounts[term] = (keywordCounts[term] || 0) + 1;
                }
            });
        }
    });

    const sortedKeywords = Object.entries(keywordCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15);

    if (sortedKeywords.length > 0) {
        html += '<div style="background:#13131f;border:1px solid #1e1e30;border-radius:10px;padding:1.5rem;margin-bottom:1rem;">';
        html += '<h3 style="color:#a5b4fc;font-size:1rem;margin-bottom:0.8rem;">📌 Most Researched Topics</h3>';
        html += '<p style="color:#777;font-size:0.82rem;margin-bottom:1rem;">The keywords and topics that appear most frequently across papers:</p>';
        html += '<div class="keyword-cloud" style="gap:0.5rem;">';
        sortedKeywords.forEach(([term, count]) => {
            const size = count >= 5 ? '1rem' : count >= 3 ? '0.9rem' : '0.82rem';
            const opacity = Math.min(1, 0.5 + (count / totalPapers));
            html += `<span class="keyword-tag" style="font-size:${size};opacity:${opacity};">${term} <small style="opacity:0.6;">(${count})</small></span>`;
        });
        html += '</div>';
        html += '</div>';
    }

    // --- Summary sentence ---
    const topMethod = sortedMethods.length > 0 ? sortedMethods[0][0] : 'N/A';
    const topTopic = sortedKeywords.length > 0 ? sortedKeywords[0][0] : 'N/A';
    html += `<div style="background:rgba(52,211,153,0.06);border:1px solid rgba(52,211,153,0.15);border-radius:10px;padding:1rem 1.2rem;">`;
    html += `<p style="color:#6ee7b7;font-size:0.9rem;">📋 <strong>Summary:</strong> Most research in this field focuses on <strong style="color:#fff;">${topTopic}</strong> using <strong style="color:#fff;">${topMethod}</strong> as the primary method. ${sortedMethods.length} unique methods were found across ${totalPapers} papers.</p>`;
    html += `</div>`;

    html += '</div>';

    // ========== SECTION 2: Future Work & Research Gaps ==========
    html += '<div class="results-section">';
    html += '<h2 style="color:#fff;font-size:1.3rem;font-weight:600;margin-bottom:0.5rem;padding-bottom:0.5rem;border-bottom:1px solid #1e1e30;"><span style="color:#6366f1;">2.</span> Future Work & Research Directions</h2>';
    html += '<p style="color:#9ca3af;font-size:0.88rem;margin-bottom:1.2rem;">Based on analyzing all papers, the following areas have less research and represent potential directions for future work.</p>';

    // --- Methods with Less Research ---
    const lessResearchedMethods = sortedMethods.filter(([m, c]) => c <= Math.max(1, Math.floor(totalPapers * 0.2)));

    if (lessResearchedMethods.length > 0) {
        html += '<div style="background:#13131f;border:1px solid #1e1e30;border-left:3px solid #f59e0b;border-radius:10px;padding:1.5rem;margin-bottom:1rem;">';
        html += '<h3 style="color:#fcd34d;font-size:1rem;margin-bottom:0.5rem;">⚠️ Methods with Limited Research</h3>';
        html += `<p style="color:#777;font-size:0.82rem;margin-bottom:1rem;">These methods are mentioned but used in very few papers (≤${Math.max(1, Math.floor(totalPapers * 0.2))} out of ${totalPapers}). More research could be done using these approaches:</p>`;
        html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">';
        lessResearchedMethods.forEach(([method, count]) => {
            html += `<div style="display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0.8rem;background:rgba(251,191,36,0.05);border:1px solid rgba(251,191,36,0.1);border-radius:8px;">`;
            html += `<span style="color:#e0e0e0;font-size:0.88rem;">${method}</span>`;
            html += `<span style="color:#9ca3af;font-size:0.75rem;">${count}/${totalPapers}</span>`;
            html += `</div>`;
        });
        html += '</div>';
        html += '</div>';
    }

    // --- Research Gaps from analysis ---
    if (gapsData && gapsData.gaps && gapsData.gaps.length > 0) {


        // Missing method combinations
        const comboGaps = gapsData.gaps.filter(g => g.type === 'missing_combinations');
        if (comboGaps.length > 0) {
            comboGaps.forEach(gap => {
                html += '<div style="background:#13131f;border:1px solid #1e1e30;border-left:3px solid #6366f1;border-radius:10px;padding:1.5rem;margin-bottom:1rem;">';
                html += '<h3 style="color:#a5b4fc;font-size:1rem;margin-bottom:0.5rem;">🔗 Unexplored Method Combinations</h3>';
                html += `<p style="color:#777;font-size:0.82rem;margin-bottom:0.8rem;">These popular methods have never been combined together in a single paper. Combining them could lead to new results:</p>`;
                if (gap.items && gap.items.length > 0) {
                    html += '<div class="keyword-cloud" style="gap:0.4rem;">';
                    gap.items.forEach(item => {
                        html += `<span class="keyword-tag method">${item}</span>`;
                    });
                    html += '</div>';
                }
                html += '</div>';
            });
        }


    }

    // --- Future Research Points ---
    html += '<div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.15);border-radius:10px;padding:1.2rem;margin-top:0.5rem;">';
    html += '<h3 style="color:#a5b4fc;font-size:1rem;margin-bottom:0.8rem;">💡 Suggested Future Research Points</h3>';
    html += '<ul style="color:#bbb;font-size:0.88rem;padding-left:1.2rem;line-height:1.8;">';

    if (lessResearchedMethods.length > 0) {
        const topUnexplored = lessResearchedMethods.slice(0, 3).map(([m]) => m).join(', ');
        html += `<li>Explore underutilized methods like <strong style="color:#fff;">${topUnexplored}</strong> which have limited coverage in current research.</li>`;
    }

    if (gapsData && gapsData.gaps) {
        const combos = gapsData.gaps.find(g => g.type === 'missing_combinations');
        if (combos && combos.items && combos.items.length > 0) {
            html += `<li>Try combining methods that haven't been used together, such as <strong style="color:#fff;">${combos.items[0]}</strong>.</li>`;
        }



        const isolated = gapsData.gaps.find(g => g.type === 'isolated_papers');
        if (isolated && isolated.items && isolated.items.length > 0) {
            html += `<li>Some papers explore unique directions that could benefit from further investigation and cross-referencing.</li>`;
        }
    }

    html += `<li>Consider applying the most popular methods to datasets or domains where they haven't been tested yet.</li>`;
    html += `<li>Compare performance of different methods on the same benchmark tasks to identify the best approaches.</li>`;
    html += '</ul>';
    html += '</div>';

    html += '</div>';

    // --- Disclaimer ---
    html += `<p style="color:#555;font-size:0.78rem;margin-top:1.5rem;font-style:italic;text-align:center;">Note: These results are automatically generated from NLP analysis of ${totalPapers} papers. Verify findings against the original papers.</p>`;

    container.innerHTML = html;
}
