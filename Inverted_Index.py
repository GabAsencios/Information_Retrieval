from bs4 import BeautifulSoup
import os
import re
from collections import defaultdict
from nltk.stem import PorterStemmer


# SUBPROJECT 1
def parse_sgm_file(filepath):
    """
      Parse all Reuters .sgm file using BeautifulSoup creating pairs of term and ID.
      Returns a dictionary (hash table) with term as key and list of docIDs as value.
      """

    # Read the file
    with open(filepath, 'r', encoding='latin-1') as f:
        content = f.read()

    print(f"File size: {len(content)} characters")

    soup = BeautifulSoup(content, "html.parser")

    docs = {}  # {docID: text}

    for reut in soup.find_all("reuters"):
        doc_id = reut.get("newid")
        text_tag = reut.find("text")
        if text_tag:
            title = text_tag.title.text if text_tag.title else ""
            body = text_tag.body.text if text_tag.body else ""
            docs[doc_id] = (title + " " + body)


    # Tokenize text/ case folding
    def tokenize(text):
        text = text.lower()
        return re.findall(r"\b[a-z0-9]+\b", text)


    # Build list of (term, docID)
    F = []  #Temporary holding for (term, docID) pairs
    for doc_id, content in docs.items():
        tokens = tokenize(content)
        for term in tokens:
            F.append((term, doc_id))

    # Sort & remove duplicates
    F = sorted(list(set(F)))


    # Build naive inverted index
    index = defaultdict(list)
    for term, doc_id in F:
        index[term].append(doc_id)


    # Print results
    print("Term-DocID pairs (F):")
    for t in F:
        print(t)

    print("\nNaive inverted index:")
    for term, postings in index.items():
        print(f"{term}: {postings}")

    return index




def process_single_term_query(index, term):
    """
    Process a single-term query on the inverted index.
    Returns the list of document IDs containing the term.

    :param index: dict -> {term: [docID1, docID2, ...]}
    :param term: str -> the query term to search for
    :return: list of document IDs
    """
    term = term.strip()  # normalize query term
    if term in index:
        return index[term]
    else:
        return []


def intersect(p1, p2):
    """
    Intersect two postings lists (p1 and p2) using the standard algorithm.
    """
    answer = []
    # Ensure lists are sorted numerically
    p1 = sorted([int(x) for x in p1])
    p2 = sorted([int(x) for x in p2])
    i = j = 0
    while i < len(p1) and j < len(p2):
        if p1[i] == p2[j]:
            answer.append(str(p1[i]))  # convert back to string for consistency
            i += 1
            j += 1
        elif p1[i] < p2[j]:
            i += 1
        else:
            j += 1
    return answer

# Parses until no more files
def uncompressed_index():

    # Path to your Reuters directory (MUST BE ON SAME DIRECTORY AS THIS FILE)
    reuters_dir = "reuters21578"

    # Loop through all Reuters .sgm files
    for filename in sorted(os.listdir(reuters_dir)):
        if filename.endswith(".sgm"):
            current_filepath = os.path.join(reuters_dir, filename)
            print(f"Parsing file: {filename}")

            # Parse each file and get its index
            index = parse_sgm_file(current_filepath)

            # Merge into global index
            for word, doc_ids in index.items():
                if word in all_documents:
                    all_documents[word].extend(doc_ids)
                else:
                    all_documents[word] = doc_ids

            print("\nFinished parsing file.")



# ============= COMPRESSION FUNCTIONS ============= #
def remove_numeric_terms(index):
    """
    Remove all numeric-only terms from the inverted index.
    Keeps terms that contain at least one letter.
    """
    filtered = {}
    for term, postings in index.items():
        # Keep term only if it contains at least one letter (not purely numeric)
        if not re.fullmatch(r'\d+', term):
            filtered[term] = postings
    return filtered


STOPWORDS_30 = {
    "the", "a", "and", "or", "is", "in", "of", "to", "that", "this",
    "it", "be", "for", "with", "on", "as", "by", "at", "from", "are",
    "was", "were", "been", "have", "has", "do", "does", "did", "an", "but"
}

STOPWORDS_150 = {
    "the", "a", "and", "or", "is", "in", "of", "to", "that", "this",
    "it", "be", "for", "with", "on", "as", "by", "at", "from", "are",
    "was", "were", "been", "have", "has", "do", "does", "did", "an", "but",
    "about", "after", "all", "between", "can", "could", "each", "few", "had", "he",
    "her", "him", "his", "how", "if", "its", "just", "no", "not", "now",
    "only", "other", "our", "out", "over", "same", "so", "some", "such", "than",
    "then", "there", "these", "they", "those", "too", "under", "very", "what", "when",
    "where", "which", "who", "why", "will", "you", "your", "would", "could", "should",
    "may", "might", "must", "shall", "can", "will", "into", "through", "during", "before",
    "after", "above", "below", "up", "down", "out", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "can", "just",
    "should", "now", "am", "being", "having", "doing", "me", "him", "her", "us",
    "them", "my", "your", "his", "her", "its", "our", "their", "what", "which",
    "who", "whom", "whose", "that", "this", "these", "those", "i", "you", "he"
}


def compress_index_30_stopwords(index):
    """
    Compress the inverted index by removing 30 common stopwords.

    :param index: dict -> {term: [docID1, docID2, ...]}
    :return: filtered dict without 30 stopwords
    """
    filtered = {}
    for term, postings in index.items():
        if term.lower() not in STOPWORDS_30:
            filtered[term] = postings
    return filtered


def compress_index_150_stopwords(index):
    """
    Compress the inverted index by removing 150 common stopwords.

    :param index: dict -> {term: [docID1, docID2, ...]}
    :return: filtered dict without 150 stopwords
    """
    filtered = {}
    for term, postings in index.items():
        if term.lower() not in STOPWORDS_150:
            filtered[term] = postings
    return filtered


def apply_stemming(index):
    """
    Apply Porter stemming to all terms in the inverted index.
    Reduces terms to their root form (e.g., "running", "runs", "ran" -> "run").

    :param index: dict -> {term: [docID1, docID2, ...]}
    :return: stemmed dict where terms are reduced to their root form
    """
    stemmer = PorterStemmer()
    stemmed = defaultdict(list)

    for term, postings in index.items():
        stemmed_term = stemmer.stem(term)
        # Combine postings from terms that stem to the same root
        stemmed[stemmed_term].extend(postings)

    # Remove duplicates in postings lists
    for term in stemmed:
        stemmed[term] = list(set(stemmed[term]))

    return dict(stemmed)

def calculate_total_postings(index):
    """Calculate total number of postings in the index."""
    return sum(len(postings) for postings in index.values())


def print_index_size(index, label):
    """
    Print the total size of an index (unique terms and total postings).

    :param index: dict -> the inverted index
    :param label: str -> description of the index
    """
    unique_terms = len(index)
    total_postings = calculate_total_postings(index)
    print(f"{label:<40} | Terms: {unique_terms:<10} | Postings: {total_postings:<12}")


def build_compressed_index(index):
    """
    Apply all compressions in sequence to build the final compressed index.
    Compressions applied: numeric removal → 30 stopwords → 150 stopwords → stemming

    :param index: dict -> the original uncompressed index
    :return: fully compressed index
    """
    # Step 1: Remove numeric terms
    compressed = remove_numeric_terms(index)

    # Step 2: Remove 30 stopwords
    compressed = compress_index_30_stopwords(compressed)

    # Step 3: Remove 150 stopwords
    compressed = compress_index_150_stopwords(compressed)

    # Step 4: Apply stemming
    compressed = apply_stemming(compressed)

    return compressed


def calculate_non_positional_postings(index):
    """
    Calculate total postings treating the index as non-positional (unique docIDs only).
    Converts each postings list to a set to remove duplicates, then counts.
    """
    return sum(len(set(postings)) for postings in index.values())


def print_non_pos_index_size(index, label):
    """
    Print unique terms and non-positional postings for the index.

    :param index: dict -> the inverted index
    :param label: str -> description of the index
    """
    unique_terms = len(index)
    non_positional_postings = calculate_non_positional_postings(index)

    print(f"{label:<40} | Terms: {unique_terms:<10} | Non-Pos Postings: {non_positional_postings:<12}")


def validate_queries_on_index(index, index_name):
    """
    Perform single-term and AND queries on a given index.

    :param index: dict -> the inverted index to query
    :param index_name: str -> name of the index for display purposes
    """
    print("\n" + "=" * 80)
    print(f"QUERY VALIDATION - {index_name}")
    print("=" * 80)

    # Validate single-term queries
    print("Single-term queries:")
    single_queries = ["bertil", "nordin", "jaguar"]
    for q in single_queries:
        results = process_single_term_query(index, q)
        print(f"  Query: '{q}' -> Documents: {results}")

    # Validate AND queries
    print("\nAND queries:")
    and_queries = [
        ["bertil", "nordin"],
        ["brazilian", "cocoa"],
        ["car", "jaguar"]
    ]
    for terms in and_queries:
        if terms[0] in index and terms[1] in index:
            results = intersect(index[terms[0]], index[terms[1]])
            print(f"  Query: {' AND '.join(terms)} -> Documents: {results}")
        else:
            missing = [t for t in terms if t not in index]
            print(f"  Query: {' AND '.join(terms)} -> Term(s) not found: {missing}")

if __name__ == "__main__":

    # Global inverted index
    all_documents = {}

    print("Parsing all Reuters .sgm files...\n")

    uncompressed_index()


    print("\nFinished parsing all files.")

    # =========== ORIGINAL INDEX QUERIES ===========
    validate_queries_on_index(all_documents, "ORIGINAL UNCOMPRESSED INDEX")

    # # Validate queries
    # print("Validating single-term queries:")
    # single_queries = ["bertil", "nordin", "jaguar"]
    # for q in single_queries:
    #     results = process_single_term_query(all_documents, q)
    #     print(f"Query: '{q}' -> Documents: {results}")
    #
    # print("\nValidating AND queries:")
    # and_queries = [
    #     ["bertil", "nordin"],
    #     ["brazilian", "cocoa"],
    #     ["car", "jaguar"]
    # ]
    # for terms in and_queries:
    #     # Check if both terms exist in the index
    #     if terms[0] in all_documents and terms[1] in all_documents:
    #         results = intersect(all_documents[terms[0]], all_documents[terms[1]])
    #         print(f"Query: {' AND '.join(terms)} -> Documents: {results}")
    #     else:
    #         missing = [t for t in terms if t not in all_documents]
    #         print(f"Query: {' AND '.join(terms)} -> Term(s) not found: {missing}")

    # # =========== Term Dictionary =========== #
    # # Create compressed index (separate from original)
    # no_numeric = remove_numeric_terms(all_documents)
    # print(f"Total unique words indexed (no numeric terms): {len(no_numeric)}")
    #
    # # Create compressed indexes for 30 and 150 stopwords
    # compressed_30 = compress_index_30_stopwords(no_numeric)
    # print(f"Total unique words indexed (30 stopwords removed): {len(compressed_30)}")
    #
    # compressed_150 = compress_index_150_stopwords(compressed_30)
    # print(f"Total unique words indexed (150 stopwords removed): {len(compressed_150)}")
    #
    # # Create stemmed index
    # stemmed_index = apply_stemming(compressed_150)
    # print(f"Total unique words indexed (Stemmed): {len(stemmed_index)}")

    # =========== BUILD COMPRESSED INDEX ===========
    print("\n" + "=" * 80)
    print("BUILDING COMPRESSED INDEX")
    print("=" * 80)
    compressed_final_index = build_compressed_index(all_documents)
    print(f"Compressed index built successfully!")
    print(f"Original index: {len(all_documents)} unique terms")
    print(f"Compressed index: {len(compressed_final_index)} unique terms")

    # =========== COMPRESSED INDEX QUERIES ===========
    validate_queries_on_index(compressed_final_index, "COMPRESSED INDEX")


    # =========== NON-POSITIONAL INDEX =========== #
    print("\n" + "=" * 80)
    print("NON-POSITIONAL INDEX - COMPRESSION CHAIN")
    print("=" * 80)
    print(f"{'Stage':<40} | {'Terms':<12} | {'Non-Pos Postings':<12}")
    print("-" * 80)

    print_non_pos_index_size(all_documents, "Case folded")

    no_pos_no_numeric = remove_numeric_terms(all_documents)
    print_non_pos_index_size(no_pos_no_numeric, "No numeric terms")

    no_pos_compressed_30 = compress_index_30_stopwords(no_pos_no_numeric)
    print_non_pos_index_size(no_pos_compressed_30, "30 stopwords removed")

    no_pos_compressed_150 = compress_index_150_stopwords(no_pos_compressed_30)
    print_non_pos_index_size(no_pos_compressed_150, "150 stopwords removed")

    no_pos_stemmed_index = apply_stemming(no_pos_compressed_150)
    print_non_pos_index_size(no_pos_stemmed_index, "Stemmed")