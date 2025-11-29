import json
from nltk.stem import PorterStemmer


def run_queries():
    # Load the index
    print("Loading index...")
    try:
        with open("index.json", "r") as f:
            inverted_index = json.load(f)
    except FileNotFoundError:
        print("Error: index.json not found. Run the spectrumspider.py first.")
        return

    # Import stemmer to reverse stemming
    stemmer = PorterStemmer()

    # Helper function to get Doc ID and Frequency
    def get_doc_details(term):
        # Stem the term to match index keys
        stemmed_term = stemmer.stem(term.lower())

        if stemmed_term in inverted_index:
            postings = inverted_index[stemmed_term]

            # Extract doc_id and frequency
            detailed_results = []
            for item in postings:
                detailed_results.append({
                    "doc_id": item['docID'],
                    "freq": item['freq']
                })
            return detailed_results
        else:
            print(f"Warning: Term '{term}' (stemmed: '{stemmed_term}') not found.")
            return []

    # Execute Queries
    details_sustainability = get_doc_details("sustainability")
    details_waste = get_doc_details("waste")


    # Intersection Algorithm (reusing from project1)
    def intersect(p1, p2):
        """
        Perform AND operation: return docIDs appearing in both postings lists.
        Converts to integers for numeric comparison, converts back to strings for consistency.
        """
        answer = []
        p1 = sorted([int(x) for x in p1])
        p2 = sorted([int(x) for x in p2])
        i = j = 0

        # Two-pointer merge algorithm
        while i < len(p1) and j < len(p2):
            if p1[i] == p2[j]:
                answer.append(str(p1[i])) # Return docID only
                i += 1
                j += 1
            elif p1[i] < p2[j]:
                i += 1
            else:
                j += 1
        return answer

    # Extract just the IDs to pass to the intersect function
    ids_sustainability = [d['doc_id'] for d in details_sustainability]
    ids_waste = [d['doc_id'] for d in details_waste]

    # Calculate intersection
    common_ids = intersect(ids_sustainability, ids_waste)
    # ---------------------------------------------------------

    print(f"\n--- Query Results ---")
    print(f"Documents containing 'sustainability': {len(details_sustainability)}")
    print(f"Documents containing 'waste': {len(details_waste)}")
    print(f"Documents containing BOTH (Intersection): {len(common_ids)}")

    # Organize the data by query word
    collection_data = {
        "sustainability": details_sustainability,
        "waste": details_waste
    }

    # Save to JSON
    with open("my_collection.json", "w") as f:
        json.dump(collection_data, f, indent=4)

    print("\nSaved 'my_collection.json' with Doc IDs and Frequencies.")


if __name__ == "__main__":
    run_queries()