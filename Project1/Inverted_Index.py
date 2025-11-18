"""
================================================================================
FILE: Inverted_Index.py
AUTHOR: Gabriel Asencios(40176253)
DATE: October 16, 2025

DESCRIPTION:
    This module implements an information retrieval system for the Reuters-21578
    corpus. It parses Reuters .sgm files to build an inverted index, supporting
    both uncompressed and compressed index variants. The program includes query
    processing (single-term and AND queries) and compression techniques such as
    case folding, stopword removal, numeric filtering, and Stemming. The program
    supports query validation and displays index size measurements as a table.

DEPENDENCIES:
    - BeautifulSoup4 (bs4): HTML/XML parsing
    - nltk: Natural Language Toolkit for stemming
    - re: Regular expressions (built-in)
    - os: File operations (built-in)
    - collections: defaultdict (built-in)

INPUT:
    - Reuters corpus located in ./reuters21578/ directory containing .sgm files

OUTPUT:
    - Uncompressed and compressed inverted indices
    - Query validation results
    - Compression statistics and index size measurements

NOTES:
    - Ensure reuters21578 directory exists in same directory as script

DISCLAIMER:
    LLMs were used to generate index size measurement table with each
    compression technique, stopwords generation, and for logic guidance.
================================================================================
"""

from bs4 import BeautifulSoup
import os
import re
from collections import defaultdict
from nltk.stem import PorterStemmer


# SUBPROJECT 1
def parse_sgm_file(filepath):
    """
    Parse Reuters .sgm file and extract (term, docID) pairs.
    Returns inverted index: {term: [docID1, docID2, ...]}
    """

    # Read file
    with open(filepath, 'r', encoding='latin-1') as f:
        content = f.read()

    print(f"File size: {len(content)} characters")

    soup = BeautifulSoup(content, "html.parser")

    # Extract title and body text from each Reuters document
    docs = {}  # {docID: text}

    for reut in soup.find_all("reuters"):
        doc_id = reut.get("newid")
        text_tag = reut.find("text")
        if text_tag:
            title = text_tag.title.text if text_tag.title else ""
            body = text_tag.body.text if text_tag.body else ""
            docs[doc_id] = (title + " " + body)


    # Generate term-docID pairs and remove duplicates
    F = []
    for doc_id, content in docs.items():
        tokens = tokenize(content)
        for term in tokens:
            F.append((term, doc_id))

    F = sorted(list(set(F)))

    # Build inverted index from term-docID pairs
    index = defaultdict(list)
    for term, doc_id in F:
        index[term].append(doc_id)

    # Display term-docID pairs (FOR TESTING)
    # print("Term-DocID pairs (F):")
    # for t in F:
    #     print(t)
    #
    # # Display inverted index (for testing)
    # print("\nNaive inverted index:")
    # for term, postings in index.items():
    #     print(f"{term}: {postings}")

    return index

# Tokenize text by splitting on non-alphanumeric characters (ignores punctuation)
def tokenize(text):
    tokens = re.split(r"[^A-Za-z0-9]+", text)
    return [t for t in tokens if t]  # Filter empty strings

def uncompressed_index(all_documents):
    """
    Iteratively parse all Reuters .sgm files in the reuters21578 directory.
    Merges term postings from all files into a single inverted index.
    """

    reuters_dir = "reuters21578"

    for filename in sorted(os.listdir(reuters_dir)):
        if filename.endswith(".sgm"):
            current_filepath = os.path.join(reuters_dir, filename)
            print(f"Parsing file: {filename}")

            # Parse file and merge its indexes into the final index
            index = parse_sgm_file(current_filepath)
            for word, doc_ids in index.items():
                if word in all_documents:
                    all_documents[word].extend(doc_ids)
                else:
                    all_documents[word] = doc_ids

            print("Finished parsing file.\n")

    return all_documents


def process_single_term_query(index, term):
    """
    Look up a single term in the index and return all docIDs containing it.
    Returns empty list if term not found.
    """
    term = term.strip()
    return index.get(term, [])

# Intersect algorithm implementation
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
            answer.append(str(p1[i]))
            i += 1
            j += 1
        elif p1[i] < p2[j]:
            i += 1
        else:
            j += 1
    return answer


# ============= COMPRESSION FUNCTIONS ============= #
def case_fold(index):
    """
    Normalize index by converting all terms to lowercase.
    Merges postings lists for terms that become identical after case folding.
    """
    folded_index = defaultdict(list)

    for term, postings in index.items():
        lower_term = term.lower()
        folded_index[lower_term].extend(postings)

    # Remove duplicate docIDs and sort numerically
    for term in folded_index:
        folded_index[term] = sorted(list(set(folded_index[term])), key=int)

    return dict(folded_index)


def remove_numeric_terms(index):
    """
    Filter out terms containing only numerical values.
    Keeps mixed terms like "abc123".
    """
    filtered = {}
    for term, postings in index.items():
        if not re.fullmatch(r'\d+', term):
            filtered[term] = postings
    return filtered


# Predefined stopword sets for different compression levels
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
    """Remove 30 most common English stopwords from the index."""
    filtered = {}
    for term, postings in index.items():
        if term.lower() not in STOPWORDS_30:
            filtered[term] = postings
    return filtered


def compress_index_150_stopwords(index):
    """Remove 150 common English stopwords for more aggressive compression."""
    filtered = {}
    for term, postings in index.items():
        if term.lower() not in STOPWORDS_150:
            filtered[term] = postings
    return filtered


def apply_stemming(index):
    """
    Reduce terms to their root form using Porter stemming (e.g., running/runs/ran → run).
    Merges postings lists for terms with identical stems.
    """
    stemmer = PorterStemmer()
    stemmed = defaultdict(list)

    for term, postings in index.items():
        stemmed_term = stemmer.stem(term)
        stemmed[stemmed_term].extend(postings)

    # Remove duplicate docIDs from merged postings
    for term in stemmed:
        stemmed[term] = list(set(stemmed[term]))

    return dict(stemmed)


def calculate_total_postings(index):
    """Sum total postings across all terms (including duplicates)."""
    return sum(len(postings) for postings in index.values())


def print_index_size(index, label):
    """Display index statistics: unique terms and total postings."""
    unique_terms = len(index)
    total_postings = calculate_total_postings(index)
    print(f"{label:<40} | Terms: {unique_terms:<10} | Postings: {total_postings:<12}")


def build_compressed_index(index):
    """
    Apply all compression techniques in sequence:
    case folds -> remove numeric terms -> 30 stopwords -> 150 stopwords -> stemming.
    """
    compressed = case_fold(index)
    compressed = remove_numeric_terms(compressed)
    compressed = compress_index_30_stopwords(compressed)
    compressed = compress_index_150_stopwords(compressed)
    compressed = apply_stemming(compressed)
    return compressed


def calculate_non_positional_postings(index):
    """
    Count unique docIDs across all terms (non-positional: duplicates removed).
    """
    return sum(len(set(postings)) for postings in index.values())


def print_non_pos_index_size(index, label):
    """Display index size numbers."""
    unique_terms = len(index)
    non_positional_postings = calculate_non_positional_postings(index)
    print(f"{label:<40} | Terms: {unique_terms:<10} | Non-Pos Postings: {non_positional_postings:<12}")


def validate_queries_on_index(index, index_name):
    """
    Test single-term and AND queries to verify index functionality.
    Confirms queries work correctly after compression transformations.
    """
    print("\n" + "=" * 80)
    print(f"QUERY VALIDATION - {index_name}")
    print("=" * 80)

    # Single-term queries: look up individual terms
    print("Single-term queries:")
    single_queries = ["copper", "Chrysler", "Bundesbank", "pineapple"]
    for q in single_queries:
        results = process_single_term_query(index, q)
        print(f"  Query: '{q}' -> Documents: {results}")

    # AND queries: uses intersect algo to intersect postings lists from multiple terms
    print("\nAND queries:")
    and_queries = [
        ["copper", "pineapple"],
        ["Bundesbank", "copper"],
        ["Chrysler", "Bundesbank"]
    ]
    for terms in and_queries:
        if terms[0] in index and terms[1] in index:
            results = intersect(index[terms[0]], index[terms[1]])
            print(f"  Query: {' AND '.join(terms)} -> Documents: {results}")
        else:
            print(f"  Query: {' AND '.join(terms)} -> []")


if __name__ == "__main__":
    # Initialize empty hashmap to store inverted index
    inverted_index = {}

    print("Parsing all Reuters .sgm files...\n")

    # Parse all files and build uncompressed inverted index
    inverted_index = uncompressed_index(inverted_index)

    print("\nFinished parsing all files.")

    # Test uncompressed index with sample queries
    validate_queries_on_index(inverted_index, "ORIGINAL UNCOMPRESSED INDEX")

    # Apply all compression techniques sequentially
    print("\n" + "=" * 80)
    print("BUILDING COMPRESSED INDEX")
    print("=" * 80)
    compressed_final_index = build_compressed_index(inverted_index) # Applies all compression techniques to build compressed index
    print(f"Compressed index built successfully!")
    print(f"Original index: {len(inverted_index)} unique terms")
    print(f"Compressed index: {len(compressed_final_index)} unique terms")

    # Test compressed index with same sample queries
    validate_queries_on_index(compressed_final_index, "COMPRESSED INDEX")

    # Display compression results showing impact of each technique
    print("\n" + "=" * 80)
    print("INVERTED INDEX - COMPRESSIONS")
    print("=" * 80)
    print(f"{'Compression':<40} | {'Term Dictionary':<17} | {'Non-Positional Postings':<12}")
    print("-" * 80)

    # Measure index size at each compression step
    print_non_pos_index_size(inverted_index, "Uncompressed")

    case_folded_index = case_fold(inverted_index)
    print_non_pos_index_size(case_folded_index, "Case folded")

    no_pos_no_numeric = remove_numeric_terms(case_folded_index)
    print_non_pos_index_size(no_pos_no_numeric, "No numeric terms")

    no_pos_compressed_30 = compress_index_30_stopwords(no_pos_no_numeric)
    print_non_pos_index_size(no_pos_compressed_30, "30 stopwords removed")

    no_pos_compressed_150 = compress_index_150_stopwords(no_pos_compressed_30)
    print_non_pos_index_size(no_pos_compressed_150, "150 stopwords removed")

    no_pos_stemmed_index = apply_stemming(no_pos_compressed_150)
    print_non_pos_index_size(no_pos_stemmed_index, "Stemmed")