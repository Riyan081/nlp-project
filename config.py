import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'researchlens.db')

# Semantic Scholar API
SEMANTIC_SCHOLAR_API = 'https://api.semanticscholar.org/graph/v1'
PAPERS_TO_FETCH = 15  # Number of papers to retrieve
API_RATE_LIMIT_DELAY = 1.0  # Seconds between API calls

# NLP Settings
SPACY_MODEL = 'en_core_web_sm'
TOP_KEYWORDS = 20  # Top TF-IDF keywords to extract per paper
TOP_GLOBAL_KEYWORDS = 30  # Top keywords across all papers

# Embedding Model
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# Clustering
DEFAULT_NUM_CLUSTERS = 3  # Default number of K-Means clusters
MAX_CLUSTERS = 5

# Research method dictionary for extraction
RESEARCH_METHODS = [
    'linear regression', 'logistic regression', 'decision tree', 'random forest',
    'gradient boosting', 'xgboost', 'lightgbm', 'catboost', 'svm', 'support vector machine',
    'naive bayes', 'knn', 'k-nearest neighbor', 'neural network', 'deep learning',
    'cnn', 'convolutional neural network', 'rnn', 'recurrent neural network',
    'lstm', 'long short-term memory', 'gru', 'transformer', 'bert', 'gpt',
    'attention mechanism', 'autoencoder', 'gan', 'generative adversarial',
    'reinforcement learning', 'transfer learning', 'ensemble', 'bagging', 'boosting',
    'arima', 'sarima', 'prophet', 'exponential smoothing',
    'pca', 'principal component', 't-sne', 'umap',
    'k-means', 'dbscan', 'hierarchical clustering', 'agglomerative clustering',
    'word2vec', 'glove', 'fasttext', 'elmo',
    'cross-validation', 'grid search', 'bayesian optimization',
    'feature engineering', 'feature selection', 'dimensionality reduction',
    'data augmentation', 'fine-tuning', 'pre-training',
]

# Research dataset keywords
RESEARCH_DATASETS = [
    'mnist', 'cifar', 'imagenet', 'coco', 'squad', 'glue', 'superglue',
    'imdb', 'yelp', 'amazon reviews', 'twitter', 'wikipedia',
    'kaggle', 'uci', 'open data', 'benchmark',
]

# Research metrics
RESEARCH_METRICS = [
    'accuracy', 'precision', 'recall', 'f1', 'f1-score', 'f-measure',
    'auc', 'roc', 'rmse', 'mae', 'mse', 'mape', 'r-squared', 'r2',
    'bleu', 'rouge', 'meteor', 'perplexity',
    'confusion matrix', 'classification report',
    'cross-entropy', 'log loss', 'hinge loss',
]

# Flask
SECRET_KEY = 'researchlens-dev-key'
DEBUG = True
