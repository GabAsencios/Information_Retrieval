import json
import matplotlib.pyplot as plt
from time import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


# ----------------------
# Data Loader
# ----------------------
class SpectrumDataset:

    def __init__(self, data, doc_ids):
        self.data = data  # List of document strings (the corpus)
        self.doc_ids = doc_ids  # List of Doc IDs (metadata)
        self.target = None  # Unsupervised, so no target class

#   Loads data from index.json and reconstructs it into a dataset object.
def fetch_spectrum_data(index_file="index.json", collection_file="my_collection.json"):

    print("Loading data from index.json...")

    try:
        with open(index_file, "r") as f:
            inverted_index = json.load(f)
        with open(collection_file, "r") as f:
            collection_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {index_file} or {collection_file}")
        exit()

    # Extract DocIDs for my_collection.json
    my_collection_ids = set()
    for query_term, doc_list in collection_data.items():
        for doc_entry in doc_list:
            # Handle both 'doc_id' and 'doc' keys for compatibility
            did = doc_entry.get("doc_id", doc_entry.get("doc"))
            if did:
                my_collection_ids.add(did)

    # Reconstruct documents as bag of words
    doc_map = {}
    for term, postings in inverted_index.items():
        for entry in postings:
            doc_id = entry['docID']
            if doc_id in my_collection_ids:
                if doc_id not in doc_map:
                    doc_map[doc_id] = []
                doc_map[doc_id].append((term + " ") * entry['freq'])

    # Create aligned lists
    data = []
    doc_ids = []
    for doc_id in sorted(doc_map.keys()):
        data.append("".join(doc_map[doc_id]))
        doc_ids.append(doc_id)

    print(f"Loaded {len(data)} documents from Spectrum.")
    return SpectrumDataset(data, doc_ids)


# ----------------------------
# Main Clustering Class
# ----------------------------
class DocumentClustering:
    def __init__(self):
        self.dataset = None
        self.X_tfidf = None
        self.vectorizer = None

    def load_data(self):
        # Use data loader
        self.dataset = fetch_spectrum_data()
    # Feature Extraction using TfidfVectorizer
    def extract_features(self):

        print("Extracting features from the dataset using a sparse vectorizer")
        t0 = time()

        self.vectorizer = TfidfVectorizer(
            max_df=0.5,  # Ignore terms frequent in over 50% of docs for better isolation of unique words
            stop_words="english",
            use_idf=True
        )

        self.X_tfidf = self.vectorizer.fit_transform(self.dataset.data)

        print(f"Vectorization done in {time() - t0:.3f} s")
        print(f"n_samples: {self.X_tfidf.shape[0]}, n_features: {self.X_tfidf.shape[1]}")
    # Runs k-means for a specific k and prints top terms.
    def run_kmeans(self, true_k):

        if true_k > self.X_tfidf.shape[0]:
            print(f"Skipping k={true_k} (n_clusters > n_samples)")
            return

        print(f"\n" + "=" * 50)
        print(f"Clustering sparse data with k-means (k={true_k})")
        print("=" * 50)

        t0 = time()

        km = KMeans(
            n_clusters=true_k,
            init="k-means++",
            max_iter=300,
            n_init=10,  # Slightly higher n_init for better stability
            verbose=False,
            random_state=42
        )

        km.fit(self.X_tfidf)
        print(f"Clustering done in {time() - t0:.3f} s")

        # ----------------------------------------
        # Top Terms per Cluster with Scores
        # ----------------------------------------
        print(f"\nTop terms per cluster:")

        # Sort cluster centers by proximity to centroid
        order_centroids = km.cluster_centers_.argsort()[:, ::-1]
        terms = self.vectorizer.get_feature_names_out()

        for i in range(true_k):
            print(f"\nCluster {i}:")
            # Get the top 20 indices for this cluster
            top_indices = order_centroids[i, :50]

            for rank, ind in enumerate(top_indices, 1):
                # Grab the score from the centroid vector
                score = km.cluster_centers_[i, ind]

                # Print Rank --> Term (Score)
                print(f" {rank}. {terms[ind]} ({score:.4f})")

        # Plotting
        self.plot_clusters(km, true_k)
    # Helper to visualize the clusters using PCA.
    def plot_clusters(self, km, k):

        # Convert sparse matrix to dense for PCA
        dense_X = self.X_tfidf.toarray()

        pca = PCA(n_components=2)
        reduced_features = pca.fit_transform(dense_X)
        reduced_centers = pca.transform(km.cluster_centers_)

        plt.figure(figsize=(10, 8))
        plt.scatter(reduced_features[:, 0], reduced_features[:, 1],
                    c=km.predict(self.X_tfidf), cmap='viridis', s=50, alpha=0.6)
        plt.scatter(reduced_centers[:, 0], reduced_centers[:, 1],
                    marker='x', s=200, c='red', label='Centroids')

        plt.title(f"K-Means Clustering (k={k})")
        plt.legend()

        filename = f"cluster_plot_k{k}.png"
        plt.savefig(filename)
        print(f"Plot saved as {filename}")
        plt.close()


# ----------------------------------
# Main Execution
# ----------------------------------
if __name__ == "__main__":
    clusterer = DocumentClustering()

    # Load Data
    clusterer.load_data()

    # Extract Features
    clusterer.extract_features()

    # Cluster for k=2, 10, 20
    for k in [2, 10, 20]:
        clusterer.run_kmeans(true_k=k)