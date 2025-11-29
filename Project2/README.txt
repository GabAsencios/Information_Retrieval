==============================================================================
PROJECT 2: WEB SCRAPING, INDEXING, AND CLUSTERING
Comp 479 - Information Retrieval
Student: Gabriel Asencios (40176253)
Date: November 28, 2025
==============================================================================

1. PROJECT OVERVIEW
------------------------------------------------------------------------------
This project implements a complete Information Retrieval pipeline designed to
crawl the Concordia Spectrum repository, index thesis documents, and perform
K-Means clustering on a specific subset of topics ("sustainability" and "waste").

The pipeline consists of three main stages:
1.  Crawling & Indexing (spectrumspider.py)
2.  Querying & Corpus Building (query_engine.py)
3.  Clustering & Visualization (clustering.py)


2. DEPENDENCIES & SETUP
------------------------------------------------------------------------------
Ensure you have Python 3.13 installed. You must install the following libraries
before running the code.

Command to install dependencies:
   pip install scrapy pymupdf nltk scikit-learn matplotlib numpy

Library Usage:
- Scrapy: Handles web crawling and spider logic.
- PyMuPDF (fitz): Extracts text from PDF files (superior to PyPDF2).
- NLTK: Provides the Porter Stemmer for term normalization.
- Scikit-Learn: Handles TF-IDF vectorization and K-Means clustering.
- Matplotlib: visualizes the clusters using PCA projection.
- NumPy: Performs numerical operations for array handling.


3. EXECUTION STEPS (DEMO WALKTHROUGH)
------------------------------------------------------------------------------
Please run the scripts in the strict order listed below. Each step generates
output files required by the next step.

STEP 1: CRAWLING & INDEXING
---------------------------
Script: spectrumspider.py
Action: Crawls the Spectrum repository, downloads PDFs, and builds the SPIMI index.

Command(inside /spectrum_spider directory):
   scrapy crawl spectrumspider -a max_documents=100

   (Note: '100' is a fair sample limit for a quick demo. For the full project results,
   a limit of 500 was used.)

Expected Output (Console):
   - Logs showing navigation to Year pages (e.g., "Queueing Year: ...")
   - Logs confirming PDF discovery (e.g., "Found PDF #1 at ...")
   - SPIMI Block flushing messages (e.g., "Flushing SPIMI block #1...")
   - Final Message: "Final index saved! X terms indexed."

Generated Files:
   - index.json: The complete inverted index.
   - blocks/: A directory containing temporary index blocks.


STEP 2: QUERYING & CORPUS CONSTRUCTION
--------------------------------------
Script: query_engine.py
Action: Loads 'index.json', queries for "sustainability" and "waste", and
        creates a sub-collection of documents.

Command:
   python query_engine.py

Expected Output (Console):
   - "Loading index..."
   - "--- Query Results ---"
   - Counts for 'sustainability' and 'waste'.
   - Final Message: "Saved 'my_collection.json' with Doc IDs and URLs."

Generated Files:
   - my_collection.json: The specific dataset used for clustering.


STEP 3: CLUSTERING & ANALYSIS
-----------------------------
Script: clustering.py
Action: Reconstructs documents from the index, applies TF-IDF vectorization,
        runs K-Means (k=2, 10, 20), and plots the results.

Command:
   python clustering.py

Expected Output (Console):
   - "Reconstructed X documents."
   - "n_samples: X, n_features: Y"
   - For each K value (2, 10, 20):
       - "Clustering done in X.XXX s"
       - A ranked list of the Top 20 terms for each cluster.
       - "Plot saved as cluster_plot_k[X].png"

Generated Files:
   - cluster_plot_k2.png
   - cluster_plot_k10.png
   - cluster_plot_k20.png


4. TROUBLESHOOTING
------------------------------------------------------------------------------
- "No blocks created":
  If the spider finishes without indexing anything, check if the website structure
  has changed or if 'max_documents' is set too low (set max_documents>=10).

- "FileNotFoundError":
  Ensure you ran the scripts in order. 'clustering.py' will fail if
  'index.json' or 'my_collection.json' do not exist or are not located in /spectrum_spider directory.

- "ValueError: n_samples=X should be >= n_clusters":
  If you only crawled a few documents (e.g., 5 docs), you cannot split them
  into 20 clusters. Increase 'max_documents' in Step 1 to at least 50.