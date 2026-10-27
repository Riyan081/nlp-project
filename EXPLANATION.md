# ResearchLens — Complete Project Explanation

> **Use this file to explain the project to your teacher.** Everything is written in simple language so you can understand it and explain it easily.

---

## 📌 What is this Project?

**ResearchLens** is a web application that helps students and researchers understand a research topic quickly.

**The simple idea:**
1. You type a research topic (example: "Machine Learning for Electricity Demand Forecasting")
2. The app automatically finds 10–15 research papers from the internet
3. It reads all the paper abstracts and analyzes them using NLP (Natural Language Processing)
4. It shows you keywords, entities, research methods, paper similarities, clusters, trends, and gaps
5. It generates a full research report you can read

**In short:** Instead of manually reading 15 papers, the app does the reading and analysis for you using NLP techniques.

---

## 🧱 Project Structure (What Each File Does)

```
ResearchLens/
├── app.py                  ← Main file. Starts the web server. Has all the URLs/routes.
├── config.py               ← All settings in one place (API URLs, model names, etc.)
├── database.py             ← All database operations (save/read papers, analyses, etc.)
├── requirements.txt        ← List of Python libraries we need to install
├── test_pipeline.py        ← Test file to check if things are working
│
├── services/               ← All the "brain" logic lives here
│   ├── paper_search.py     ← Finds papers from Semantic Scholar / OpenAlex APIs
│   ├── nlp.py              ← NLP analysis: tokenization, TF-IDF, NER, POS tagging
│   ├── similarity.py       ← Creates embeddings and computes paper similarity
│   └── analysis.py         ← Clustering, trends, gap analysis, methodology comparison
│
├── templates/              ← HTML pages (what the user sees)
│   ├── index.html          ← Home page with search box
│   ├── dashboard.html      ← Main dashboard with tabs (papers, keywords, clusters, etc.)
│   └── report.html         ← The final research report page
│
├── static/                 ← Frontend files
│   ├── style.css           ← All the styling (colors, layout, fonts)
│   └── app.js              ← JavaScript that makes the dashboard interactive
│
└── data/
    └── researchlens.db     ← SQLite database file (stores all papers and results)
```

---

## 🛠️ Technologies Used (What & Why)

### Backend (Server Side)

| Technology | What is it? | Why we used it? |
|-----------|-------------|-----------------|
| **Python** | Programming language | Best language for NLP and data processing. Has lots of NLP libraries. |
| **Flask** | Web framework | Simple and lightweight. Easy to learn. Creates web server with just a few lines of code. |
| **SQLite** | Database | Comes built-in with Python. No need to install a separate database server. Stores data in a single file. |

### NLP Libraries

| Library | What is it? | Why we used it? |
|---------|-------------|-----------------|
| **spaCy** | NLP toolkit | Does tokenization, lemmatization, NER, and POS tagging. Very fast and accurate. |
| **scikit-learn** | Machine Learning library | Has TF-IDF, K-Means clustering, and cosine similarity functions ready to use. |
| **sentence-transformers** | Embedding library | Converts text into number vectors (embeddings) so we can compare papers by meaning, not just words. Uses a pre-trained BERT-based model. |
| **NLTK** | NLP toolkit | Additional NLP utilities. |
| **NumPy** | Math library | For handling arrays and mathematical operations on embedding vectors. |

### Frontend (What User Sees)

| Technology | What is it? | Why we used it? |
|-----------|-------------|-----------------|
| **HTML** | Page structure | Creates the structure of web pages. |
| **CSS** | Page styling | Makes the pages look beautiful (colors, layout, fonts). |
| **JavaScript** | Page logic | Makes the dashboard interactive (tab switching, button clicks, API calls). |
| **Chart.js** | Chart library | Creates beautiful charts (bar charts, pie charts, heatmaps) for data visualization. |

### APIs (External Services)

| API | What is it? | Why we used it? |
|-----|-------------|-----------------|
| **Semantic Scholar API** | Academic paper database | Free API to search and get research papers. Gives us title, abstract, authors, year, citations. |
| **OpenAlex API** | Backup paper database | If Semantic Scholar fails (rate limiting), we use this as a backup. Also free. |

### Models (Pre-trained AI Models)

| Model | What is it? | Why we used it? |
|-------|-------------|-----------------|
| **en_core_web_sm** | spaCy's English model | Pre-trained model that understands English text. Does tokenization, NER, POS tagging. |
| **all-MiniLM-L6-v2** | Sentence Transformer model | Converts sentences into 384-dimension vectors. Trained on 1 billion+ sentence pairs. Understands meaning, not just words. |

---

## 🔄 How the Project Works — Complete Flow

Here is the step-by-step flow from when the user types a topic to when they see results:

### Step 1: User Enters a Topic

- User opens `http://localhost:5000` in browser
- They see the home page (`index.html`) with a search box
- They type something like **"Machine Learning for Electricity Demand Forecasting"**
- They click **"Discover Papers"**

**What happens in the code:**
- The form sends a POST request to `/search` route in `app.py`
- `app.py` calls `search_papers()` from `services/paper_search.py`

### Step 2: Finding Papers (Paper Discovery)

**File:** `services/paper_search.py`

The app searches for papers in this order:

1. **First try:** Semantic Scholar API
   - Sends the topic as a search query to `https://api.semanticscholar.org/graph/v1/paper/search`
   - Gets back paper data: title, abstract, authors, year, citations, URLs
   - Only keeps papers that have abstracts (papers without abstract are useless for our NLP)

2. **If Semantic Scholar fails** (e.g., rate limited — too many requests):
   - Falls back to OpenAlex API (`https://api.openalex.org/works`)
   - OpenAlex stores abstracts in a special "inverted index" format, so we need to reconstruct them

3. **Deduplication:**
   - Removes duplicate papers (same title in different sources)
   - Normalizes titles (lowercase, remove special characters) to catch duplicates

4. **Ranking:**
   - Each paper gets a **relevance score** based on:
     - **Title overlap** with the search topic (40% weight) — more matching words = higher score
     - **Abstract overlap** with the search topic (20% weight)
     - **Citation count** (log-scaled) — highly cited papers get a boost
     - **Recency** — newer papers (2020+) get extra points
     - **Abstract quality** — papers with longer abstracts score slightly higher
   - Papers are sorted by score, top 15 are selected

5. **Saving to database:**
   - A new "session" is created in the database
   - All 15 papers are saved to the `papers` table
   - Papers are linked to the session in `session_papers` table

**After this step:** User is redirected to the **dashboard** page and can see all 15 papers with their metadata.

### Step 3: NLP Analysis (When User Clicks "Run NLP Analysis")

When the user clicks the "🧠 Run NLP Analysis" button on the dashboard, JavaScript sends a POST request to `/api/analyze/<session_id>`. This triggers a 7-step analysis pipeline:

---

#### Step 3.1: Text Preprocessing (spaCy)

**File:** `services/nlp.py` | **Library:** spaCy

What happens to each paper's abstract:

```
Raw text: "The proposed LSTM models achieve high accuracy in forecasting electricity demands."
    ↓
Tokenization: ["The", "proposed", "LSTM", "models", "achieve", "high", "accuracy", "in", "forecasting", "electricity", "demands", "."]
    ↓
Lemmatization: ["propose", "lstm", "model", "achieve", "high", "accuracy", "forecast", "electricity", "demand"]
    ↓
Stop word removal: (removes "The", "in" — common words with no meaning)
    ↓
Sentence segmentation: Splits text into individual sentences
```

**Why we do this:**
- Raw text is messy. "predict", "predicts", "predicted", "predicting" are all the same concept
- Lemmatization reduces them all to "predict"
- Stop words like "the", "is", "and" don't carry useful meaning — removing them gives better results
- This cleaned text is used by all the following NLP steps

---

#### Step 3.2: TF-IDF Keyword Extraction

**File:** `services/nlp.py` | **Library:** scikit-learn (TfidfVectorizer)

**What is TF-IDF?**
- TF = **Term Frequency** — How many times a word appears in ONE paper
- IDF = **Inverse Document Frequency** — How rare a word is across ALL papers
- TF-IDF = TF × IDF

**Simple example:**
- The word "learning" appears in all 15 papers → IDF is low → TF-IDF score is LOW
- The word "XGBoost" appears in only 2 papers → IDF is high → TF-IDF score is HIGH
- So "XGBoost" is a more meaningful keyword than "learning"

**What we extract:**
1. **Per-paper keywords:** Top 20 keywords for each paper (unigrams + bigrams)
2. **Global keywords:** Top 30 keywords across all 15 papers (unigrams + bigrams + trigrams)

**Parameters used:**
- `ngram_range=(1, 3)` — Extract single words, 2-word phrases, and 3-word phrases
- `max_features=500` — Only consider top 500 terms
- `stop_words='english'` — Remove common English words
- `max_df=0.95` — Ignore words that appear in more than 95% of documents

---

#### Step 3.3: Named Entity Recognition (NER)

**File:** `services/nlp.py` | **Library:** spaCy

**What is NER?**
NER automatically finds and labels "names" in text:
- **ORG** → Organizations (e.g., "IEEE", "Google", "MIT")
- **GPE** → Places (e.g., "China", "Europe", "USA")
- **PERSON** → People's names
- **DATE** → Dates (e.g., "2023", "last decade")
- **CARDINAL** → Numbers

**Example:**
```
Text: "Google researchers in California used BERT for NLP tasks in 2023"
NER output:
  - "Google" → ORG
  - "California" → GPE
  - "2023" → DATE
```

**Why we use it:**
It automatically discovers which organizations, locations, and people are mentioned across all the research papers.

---

#### Step 3.4: POS Tagging (Part-of-Speech)

**File:** `services/nlp.py` | **Library:** spaCy

**What is POS tagging?**
It labels each word with its grammar type:
- **NOUN** → model, data, algorithm
- **VERB** → predict, train, evaluate
- **ADJ** → accurate, robust, novel

**Example:**
```
"The model predicts accurate results"
  The → DET (determiner)
  model → NOUN
  predicts → VERB
  accurate → ADJ
  results → NOUN
```

**Why we use it:**
- Helps spaCy do better NER
- Helps us understand the writing style and structure of abstracts
- Used internally by other spaCy features

---

#### Step 3.5: Dictionary-Based Extraction (Methods, Datasets, Metrics)

**File:** `services/nlp.py` + `config.py`

We have 3 hand-made dictionaries in `config.py`:

| Dictionary | Examples | Count |
|-----------|----------|-------|
| **Research Methods** | random forest, LSTM, XGBoost, transformer, CNN, BERT | 42 methods |
| **Datasets** | MNIST, ImageNet, CIFAR, IMDB, Kaggle | 16 datasets |
| **Metrics** | accuracy, F1-score, RMSE, AUC, precision, recall | 18 metrics |

**How it works:**
- For each paper abstract, we do **case-insensitive string matching** against these dictionaries
- If "random forest" appears in the abstract → we record it as a method used in that paper

**Why not just use NER for this?**
- spaCy's general NER can't reliably detect domain-specific terms like "XGBoost" or "RMSE"
- These terms are not people/places/organizations, so NER misses them
- Dictionary matching is simple but very effective for known technical terms

---

#### Step 3.6: Sentence Embeddings (Transformer)

**File:** `services/similarity.py` | **Library:** sentence-transformers | **Model:** all-MiniLM-L6-v2

**What are embeddings?**
- An embedding converts text into a **list of numbers** (a vector)
- Our model converts each abstract into a **384-dimensional vector**
- Papers about similar topics will have similar vectors

**Simple analogy:**
Think of each paper as a point in space. Papers about the same thing will be close together. Papers about different things will be far apart.

**Why embeddings are better than keyword matching:**
- "electricity demand prediction" and "power consumption forecasting" have **ZERO words in common**
- But their embeddings will be very **similar** because they mean the same thing
- Embeddings understand **meaning**, not just words

**The model (all-MiniLM-L6-v2):**
- Based on BERT (a famous transformer model by Google)
- Distilled (compressed) version — small and fast
- Trained on 1 billion+ sentence pairs
- Output: 384 numbers per sentence

**Code flow:**
```
Abstract text → Tokenize → Pass through 6 transformer layers → Pool → 384-dim vector
```

The embeddings are saved in the database as binary data so we don't have to recalculate them.

---

#### Step 3.7: Cosine Similarity Matrix

**File:** `services/similarity.py` | **Library:** scikit-learn

**What is cosine similarity?**
It measures how similar two vectors are:
- **1.0** = Identical meaning
- **0.5** = Somewhat related
- **0.0** = Completely different

**Formula:**
```
similarity(A, B) = (A · B) / (|A| × |B|)
```
(Dot product of vectors divided by their magnitudes)

**What we build:**
A **15×15 matrix** where each cell `[i][j]` tells how similar paper `i` is to paper `j`.

Example (simplified 3×3):
```
         Paper 1   Paper 2   Paper 3
Paper 1    1.00      0.85      0.32
Paper 2    0.85      1.00      0.45
Paper 3    0.32      0.45      1.00
```
→ Paper 1 and Paper 2 are very similar (0.85)
→ Paper 1 and Paper 3 are quite different (0.32)

This matrix is displayed as a **heatmap** on the dashboard.

---

### Step 4: Clustering (K-Means)

**File:** `services/analysis.py` | **Library:** scikit-learn (KMeans)

**What is K-Means clustering?**
It groups papers into **clusters** (themes) based on their embeddings.

**How K-Means works (simple version):**
1. Pick 3 random center points (centroids)
2. Assign each paper to the nearest center point
3. Move the center points to the average of their assigned papers
4. Repeat steps 2–3 until nothing changes

**Result:** Papers are grouped into 3 clusters. For example:
- **Cluster 1:** Deep learning papers (LSTM, CNN)
- **Cluster 2:** Traditional ML papers (Random Forest, XGBoost)
- **Cluster 3:** Statistical methods (ARIMA, exponential smoothing)

**Cluster labeling:**
Each cluster gets a name from its top TF-IDF keywords.

**Parameters:**
- `n_clusters=3` — We create 3 groups (can be up to 5)
- `random_state=42` — Makes results reproducible (same input = same output every time)
- `n_init=10` — Runs the algorithm 10 times, picks the best result

---

### Step 5: Trend Analysis

**File:** `services/analysis.py`

**What it does:**
- Counts how many papers were published each year
- Tracks which methods appear in which years
- Tracks which keywords appear in which years

**Example output:**
```
2019: 2 papers (mostly ARIMA, SVM)
2020: 3 papers (LSTM appears for first time)
2021: 4 papers (transformer, BERT start appearing)
2022: 3 papers (mostly deep learning)
2023: 3 papers (XGBoost, hybrid methods)
```

This helps us see **how research is changing over time** — e.g., "deep learning is becoming more popular, traditional statistics is declining."

---

### Step 6: Underrepresented Themes

**File:** `services/analysis.py`

**What it does:**
Finds methods and keywords that appear in very few papers (less than 20% of total papers).

**Example:**
- "weather variables" → appears in 2/15 papers (13%) → **underrepresented**
- "random forest" → appears in 8/15 papers (53%) → common, not underrepresented

**Why it's useful:**
These underrepresented themes could be areas where more research is needed (potential research gaps).

**Important note:** We say "potentially underrepresented" — we can't prove these are real research gaps from just 15 papers.

---

### Step 7: Research Gap Analysis

**File:** `services/analysis.py`

This is the most advanced analysis. It identifies 5 types of gaps:

| Gap Type | How it's Detected | Example |
|----------|-------------------|---------|
| **Underexplored Methods** | Methods in <15% of papers | "GAN appears in only 1 paper" |
| **Declining Themes** | Keywords in old papers but not in recent 2 years | "SVM was popular in 2018-2019 but absent in 2022-2023" |
| **Cross-Cluster Gaps** | Methods found in only one cluster | "ARIMA is only used in the statistics cluster, never with deep learning" |
| **Isolated Papers** | Papers with low average similarity to others (<0.4) | "Paper X has very different topic from all other papers" |
| **Unexplored Combinations** | Popular methods that are never combined in same paper | "Random Forest + LSTM are both popular but never used together" |

Each gap is also given a **severity** (high / medium / low).

---

### Step 8: Methodology Comparison

**File:** `services/analysis.py`

Builds a comparison table showing for each paper:
- What methods it uses
- What datasets it uses
- What evaluation metrics it uses
- Its citation count and year

This makes it easy to compare what different papers are doing.

---

### Step 9: Semantic Search

**File:** `services/similarity.py`

**What it does:**
Lets users type a natural language question and find relevant papers.

**How it works:**
1. User types: "Which papers use weather data?"
2. The query is converted to an embedding using the same model
3. We compute cosine similarity between the query embedding and all paper embeddings
4. Papers are ranked by similarity
5. Top 5 most relevant papers are shown

**Why it's better than keyword search:**
- Keyword search for "weather" would miss papers that say "meteorological" or "climate"
- Semantic search understands they mean similar things and finds those papers too

---

### Step 10: Dashboard & Report

**Dashboard** (`templates/dashboard.html` + `static/app.js`):
- Has tabs: Papers, Keywords, Clusters, Trends, Results, Semantic Search
- Shows charts using Chart.js (bar charts, pie charts, heatmaps)
- All data comes from the API endpoints via JavaScript fetch calls

**Report** (`templates/report.html`):
- A structured research report page
- Shows topic, papers, themes, methods, trends, gaps
- Can be viewed in the browser

---

## 🗄️ Database Design

We use **SQLite** — a simple file-based database. All data is stored in `data/researchlens.db`.

### Tables:

| Table | What it Stores | Key Columns |
|-------|---------------|-------------|
| **research_sessions** | Each search the user does | id, topic, created_at, num_papers, status |
| **papers** | Individual research papers | id, external_id, title, abstract, authors, year, venue, doi, url, citation_count |
| **session_papers** | Links papers to sessions (many-to-many) | session_id, paper_id, relevance_score |
| **paper_analysis** | NLP analysis results for each paper | session_id, paper_id, keywords, entities, methods, datasets, metrics, pos_tags |
| **paper_embeddings** | Embedding vectors (stored as binary) | session_id, paper_id, embedding |
| **topics** | Extracted research themes/clusters | session_id, topic_name, frequency, paper_ids |

### Why this design?
- **research_sessions** allows search history (you can go back to previous searches)
- **papers** stores each paper only once (even if it appears in multiple searches) — deduplication
- **session_papers** is a "junction table" — it connects sessions and papers with a relevance score
- **paper_analysis** stores all NLP results so we don't have to re-run analysis every time
- **paper_embeddings** stores vectors as binary (BLOB) so we don't have to re-compute them

---

## 🌐 Web Routes (URLs)

The web app has these routes (defined in `app.py`):

| URL | Method | What it Does |
|-----|--------|--------------|
| `/` | GET | Home page — shows search box and past sessions |
| `/search` | POST | Takes the topic, fetches papers, creates a session, redirects to dashboard |
| `/dashboard/<session_id>` | GET | Shows the dashboard for a specific session |
| `/api/analyze/<session_id>` | POST | Runs the full NLP analysis pipeline (called by JavaScript) |
| `/api/results/<session_id>` | GET | Loads previously saved analysis results |
| `/api/semantic-search/<session_id>` | POST | Runs semantic search with a user query |
| `/report/<session_id>` | GET | Shows the research report page |

---

## 📊 NLP Techniques Summary

Here's a quick reference of ALL the NLP techniques we use:

| # | Technique | Library | What it Does | Where in Code |
|---|-----------|---------|--------------|---------------|
| 1 | Tokenization | spaCy | Splits text into words | `services/nlp.py` |
| 2 | Lemmatization | spaCy | Reduces words to base form ("running" → "run") | `services/nlp.py` |
| 3 | Stop Word Removal | spaCy | Removes common words (the, is, and) | `services/nlp.py` |
| 4 | Sentence Segmentation | spaCy | Splits text into sentences | `services/nlp.py` |
| 5 | POS Tagging | spaCy | Labels words as NOUN, VERB, ADJ, etc. | `services/nlp.py` |
| 6 | Named Entity Recognition | spaCy | Finds names, organizations, places | `services/nlp.py` |
| 7 | TF-IDF | scikit-learn | Finds important keywords per paper and globally | `services/nlp.py` |
| 8 | N-grams | scikit-learn | Extracts multi-word phrases (bigrams, trigrams) | `services/nlp.py` |
| 9 | Dictionary Matching | Custom code | Finds research methods, datasets, metrics | `services/nlp.py` + `config.py` |
| 10 | Sentence Embeddings | sentence-transformers | Converts text to 384-dim meaning vectors | `services/similarity.py` |
| 11 | Cosine Similarity | scikit-learn | Measures how similar two papers are | `services/similarity.py` |
| 12 | K-Means Clustering | scikit-learn | Groups papers into themes | `services/analysis.py` |
| 13 | Semantic Search | sentence-transformers + sklearn | Find papers by meaning, not keywords | `services/similarity.py` |
| 14 | Trend Analysis | Custom code | Tracks methods/themes over years | `services/analysis.py` |
| 15 | Gap Analysis | Custom code | Finds underexplored areas in literature | `services/analysis.py` |

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        USER (Browser)                       │
│  types topic → sees dashboard → views charts → reads report │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP Requests
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Web Server (app.py)                 │
│                                                             │
│  Routes:  /  /search  /dashboard  /api/analyze  /report     │
└────────┬──────────┬──────────┬──────────┬───────────────────┘
         │          │          │          │
         ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  paper   │ │   nlp    │ │similarity│ │ analysis │
│_search.py│ │   .py    │ │   .py    │ │   .py    │
│          │ │          │ │          │ │          │
│ Semantic │ │ spaCy    │ │Sentence  │ │ K-Means  │
│ Scholar  │ │ TF-IDF   │ │Transform │ │ Trends   │
│ OpenAlex │ │ NER      │ │ Cosine   │ │ Gaps     │
│ Ranking  │ │ POS      │ │ Sim      │ │ Compare  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
         │          │          │          │
         └──────────┴──────────┴──────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │   SQLite Database    │
              │  (researchlens.db)   │
              │                      │
              │ sessions, papers,    │
              │ analyses, embeddings │
              └──────────────────────┘
```

---

## 🚀 How to Run the Project

```bash
# Step 1: Install Python libraries
pip install -r requirements.txt

# Step 2: Download the spaCy English model
python -m spacy download en_core_web_sm

# Step 3: Run the app
python app.py

# Step 4: Open in browser
# Go to http://localhost:5000
```

---

## 💡 Key Design Decisions (Why We Did Things This Way)

### 1. Why abstracts, not full papers?
- Full paper PDFs need complex parsing (PyMuPDF, PDF layout analysis)
- Many papers are behind paywalls (not freely available)
- Abstracts contain the most important information in condensed form
- For a mini-project, abstracts are enough to demonstrate all NLP techniques

### 2. Why pre-trained models instead of training our own?
- Training a transformer model needs millions of data points and expensive GPUs
- Pre-trained models like `all-MiniLM-L6-v2` are already trained on 1 billion+ sentences
- They work well out-of-the-box for our use case
- **Focus of the project** is demonstrating NLP techniques, not training models

### 3. Why dictionary matching for methods instead of training a custom NER model?
- Training a custom NER model needs thousands of labeled examples
- Dictionary matching is simple, reliable, and easy to understand
- We can easily add new methods to the dictionary in `config.py`
- For research-specific terms (XGBoost, RMSE), dictionary matching works better than general NER

### 4. Why SQLite instead of PostgreSQL or MySQL?
- SQLite is built into Python — zero installation needed
- Data is stored in a single file (`researchlens.db`)
- Perfect for a project of this size (15 papers per session)
- Easy to demo on any computer

### 5. Why Flask instead of Django?
- Flask is minimal and lightweight — less boilerplate code
- Our project has only a few routes (7 URLs)
- Flask gives us full control without enforcing a specific project structure
- Easier to understand for learning purposes

### 6. Why 2 APIs (Semantic Scholar + OpenAlex)?
- Semantic Scholar has rate limits (429 Too Many Requests)
- OpenAlex is completely free with no rate limits
- Having a fallback ensures the app always works
- Both APIs return similar data (title, abstract, authors, year)

---

## ❓ Common Questions a Teacher Might Ask

### Q: "What NLP techniques are used in this project?"
**A:** We use 15 NLP techniques:
1. Tokenization, Lemmatization, Stop word removal (text preprocessing with spaCy)
2. POS Tagging, Sentence Segmentation (linguistic analysis with spaCy)
3. Named Entity Recognition / NER (extracting names, organizations with spaCy)
4. TF-IDF (finding important keywords with scikit-learn)
5. N-grams (extracting multi-word phrases)
6. Dictionary-based Information Extraction (finding methods, datasets, metrics)
7. Sentence Embeddings (converting text to meaning vectors using transformer model)
8. Cosine Similarity (comparing papers mathematically)
9. K-Means Clustering (grouping similar papers)
10. Semantic Search (finding papers by meaning)
11. Trend Analysis, Gap Analysis (custom algorithms)

### Q: "What is the difference between classical NLP and modern NLP in your project?"
**A:**
- **Classical NLP:** TF-IDF, NER, POS tagging, tokenization, lemmatization. These work with exact words and rules.
- **Modern NLP:** Sentence embeddings using transformers (BERT-based model). These understand meaning and context, not just words. "electricity prediction" and "power forecasting" will be recognized as similar.
- Our project **combines both** — classical NLP for extracting specific information, modern NLP for understanding relationships.

### Q: "How does your project handle the cold-start problem (no data initially)?"
**A:** There is no cold-start problem because:
- We fetch papers fresh from APIs each time
- We use pre-trained models (spaCy, sentence-transformers) — no training data needed
- The system works from the very first search

### Q: "What are the limitations of this project?"
**A:**
1. We only analyze abstracts, not full papers (limited information)
2. We depend on API availability (if both APIs are down, no results)
3. Research gaps are "potentially underrepresented" — not proven gaps
4. NLP can make mistakes (NER might misidentify entities)
5. We use only 15 papers — a real literature review needs hundreds
6. Dictionary matching only finds known methods — it can't discover new ones

### Q: "Why is this project important / what problem does it solve?"
**A:** A student doing a literature review has to:
- Search multiple sources for papers
- Read 15+ abstracts manually
- Identify methods, datasets, and metrics from each paper
- Compare papers and find themes
- Track trends over years
- Write a structured report

ResearchLens automates all of this using NLP. It doesn't replace human judgment, but it gives a **structured starting point** that saves hours of manual work.

### Q: "What makes your project different from just using Google Scholar?"
**A:** Google Scholar only finds papers. Our project finds papers AND:
- Extracts keywords, entities, methods, datasets, metrics automatically
- Compares papers semantically (by meaning, not just keywords)
- Groups papers into research themes (clustering)
- Shows research trends over time
- Identifies potentially underexplored areas
- Generates a structured research report
- Lets you search by meaning (semantic search)

---

## 📝 Summary (One Paragraph)

ResearchLens is an NLP-based web application built with Python (Flask) that automatically discovers 10–15 research papers for a user-provided topic using academic APIs (Semantic Scholar, OpenAlex), analyzes them using multiple NLP techniques including tokenization, lemmatization, POS tagging, Named Entity Recognition (spaCy), TF-IDF keyword extraction (scikit-learn), sentence embeddings (sentence-transformers with all-MiniLM-L6-v2 model), cosine similarity, K-Means clustering, dictionary-based information extraction, and semantic search. The results are stored in an SQLite database and presented through an interactive dashboard with Chart.js visualizations, showing paper details, extracted keywords and entities, research clusters, methodology comparisons, research trends over time, and potential research gaps. The project combines classical NLP with modern deep learning techniques to transform unstructured research literature into a structured, interactive research landscape.
