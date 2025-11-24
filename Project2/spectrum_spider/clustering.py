import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


# ---------------------------------------------------------
# 1. SETUP & LOADING
# ---------------------------------------------------------
def load_data():
    print("Loading index and collection...")
    try:
        with open("index.json", "r") as f:
            inverted_index = json.load(f)

        # Load the dictionary format (Query -> List of Docs)
        with open("my_collection.json", "r") as f:
            collection_data = json.load(f)

        # Extract unique Document IDs
        my_collection_ids = set()
        for query_term, doc_list in collection_data.items():
            for doc_entry in doc_list:
                if "doc_id" in doc_entry:
                    my_collection_ids.add(doc_entry["doc_id"])

    except FileNotFoundError:
        print("Error: Files not found. Run the spider and query_engine.py first.")
        exit()

    print(f"Loaded index with {len(inverted_index)} terms.")
    print(f"Targeting 'My-collection' with {len(my_collection_ids)} unique documents.")
    return inverted_index, my_collection_ids


# ---------------------------------------------------------
# 2. DOCUMENT RECONSTRUCTION
# ---------------------------------------------------------
def reconstruct_documents(inverted_index, my_collection_ids):
    print("Reconstructing pseudo-documents from index...")
    doc_content_map = {doc_id: [] for doc_id in my_collection_ids}

    for term, postings in inverted_index.items():
        for entry in postings:
            doc_id = entry['doc']
            freq = entry['freq']
            if doc_id in my_collection_ids:
                doc_content_map[doc_id].extend([term] * freq)

    final_corpus = []
    final_doc_ids = []
    for doc_id, token_list in doc_content_map.items():
        final_corpus.append(" ".join(token_list))
        final_doc_ids.append(doc_id)

    return final_corpus, final_doc_ids


# ---------------------------------------------------------
# 3. PLOTTING FUNCTION
# ---------------------------------------------------------
def plot_clusters(X, labels, k, centers):
    """
    Reduces dimensions to 2D using PCA and plots the clusters.
    """
    print(f"Generating plot for k={k}...")

    # Reduce dimensions: High-Dim TF-IDF -> 2D (x, y)
    # We use .toarray() because PCA expects a dense matrix
    pca = PCA(n_components=2)
    reduced_features = pca.fit_transform(X.toarray())

    # Reduce the cluster centers too so we can plot "X" marks
    reduced_centers = pca.transform(centers)

    plt.figure(figsize=(10, 8))

    # Plot each point (document)
    # c=labels assigns a color based on the cluster ID
    scatter = plt.scatter(reduced_features[:, 0], reduced_features[:, 1],
                          c=labels, cmap='viridis', alpha=0.6)

    # Plot the centroids (the center of each cluster)
    plt.scatter(reduced_centers[:, 0], reduced_centers[:, 1],
                marker='x', s=200, linewidths=3, color='red', label='Centroids')

    plt.title(f"Document Clusters (k={k}) Visualized with PCA")
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.colorbar(scatter, label="Cluster Label")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Save the plot
    filename = f"cluster_plot_k{k}.png"
    plt.savefig(filename)
    print(f"Plot saved as {filename}")
    plt.show() # Uncomment if you want to see the window pop up


# ---------------------------------------------------------
# 4. MAIN CLUSTERING LOGIC
# ---------------------------------------------------------
def print_top_terms(km, vectorizer, k):
    print(f"\n--- Top terms for k={k} clusters ---")
    order_centroids = km.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()
    for i in range(k):
        top_terms = [terms[ind] for ind in order_centroids[i, :50]]
        print(f"Cluster {i}: {', '.join(top_terms)}")


def main():
    inverted_index, my_collection_ids = load_data()

    # 1. Reconstruct
    corpus, doc_ids = reconstruct_documents(inverted_index, my_collection_ids)
    if not corpus:
        print("Error: Corpus is empty.")
        exit()

    # 2. Vectorize (TF-IDF)
    print("Vectorizing documents...")
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(corpus)

    # 3. Run KMeans
    k_values = [2, 10, 20]
    for k in k_values:
        print(f"\nRunning KMeans clustering with k={k}...")
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X)

        # Print Terms
        print_top_terms(km, vectorizer, k)

        # Plot Results
        plot_clusters(X, km.labels_, k, km.cluster_centers_)


if __name__ == "__main__":
    main()