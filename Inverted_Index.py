from bs4 import BeautifulSoup
import os
import re
from collections import defaultdict

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
            docs[doc_id] = (title + " " + body).lower()


    # Tokenize text
    def tokenize(text):
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
    term = term.lower().strip()  # normalize query term
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
def process_all():

    # Path to your Reuters directory (MUST BE ON SAME DIRECTORY AS THIS FILE)
    reuters_dir = "Reuters-21578"

    # Loop through all Reuters .sgm files
    for filename in os.listdir(reuters_dir):
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

            print("\nFinished parsing all files.")
            print(f"Total unique words indexed: {len(all_documents)}\n")


if __name__ == "__main__":

    # Global inverted index
    all_documents = {}

    print("Parsing all Reuters .sgm files...\n")

    process_all()

    print("\nFinished parsing all files.")
    print(f"Total unique words indexed: {len(all_documents)}\n")


    # Validate queries
    print("Validating single-term queries:")
    single_queries = ["bertil", "jaguar", "nordin"]
    for q in single_queries:
        results = process_single_term_query(all_documents, q)
        print(f"Query: '{q}' -> Documents: {results}")

    print("\nValidating AND queries:")
    and_queries = [
        ["bertil", "nordin"],
        ["brazilian", "cocoa"],
        ["car", "jaguar"]
    ]
    for terms in and_queries:
        results = intersect(all_documents[terms[0]], all_documents[terms[1]])
        print(f"Query: {' AND '.join(terms)} -> Documents: {results}")
