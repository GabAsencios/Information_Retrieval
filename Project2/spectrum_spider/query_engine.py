import json
from nltk.stem import PorterStemmer


def run_queries():
    # Load the index
    print("Loading index...")
    try:
        with open("index.json", "r") as f:
            inverted_index = json.load(f)
    except FileNotFoundError:
        print("Error: index.json not found. Run the spider first.")
        return

    stemmer = PorterStemmer()

    # Helper function to get ONLY Doc ID and URL
    def get_doc_details(term):
        # Stem the term to match index keys
        stemmed_term = stemmer.stem(term.lower())

        if stemmed_term in inverted_index:
            postings = inverted_index[stemmed_term]

            # Extract only doc_id and url
            detailed_results = []
            for item in postings:
                detailed_results.append({
                    "doc_id": item['doc'],
                    "url": item['url']
                })
            return detailed_results
        else:
            print(f"Warning: Term '{term}' (stemmed: '{stemmed_term}') not found.")
            return []

    # Execute Queries
    details_sustainability = get_doc_details("sustainability")
    details_waste = get_doc_details("waste")

    print(f"\n--- Query Results ---")
    print(f"Documents containing 'sustainability': {len(details_sustainability)}")
    print(f"Documents containing 'waste': {len(details_waste)}")

    # Organize the data by query word
    collection_data = {
        "sustainability": details_sustainability,
        "waste": details_waste
    }

    # Save to JSON
    with open("my_collection.json", "w") as f:
        json.dump(collection_data, f, indent=4)

    print("\nSaved 'my_collection.json' with Doc IDs and URLs.")


if __name__ == "__main__":
    run_queries()