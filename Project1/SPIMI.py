
"""
================================================================================
FILE: SPIMI.py
AUTHOR: Gabriel Asencios (40176253)
DATE: October 16, 2025

DESCRIPTION:
    Compares two indexing algorithms on Reuters-21578 corpus:
    1. Traditional indexing: collect pairs -> sort -> deduplicate -> build
    2. SPIMI: process sequentially -> append docIDs directly to hash table

PERFORMANCE RESULTS:
    - Traditional: 25 seconds
    - SPIMI: 130 seconds (5.1x slower)
    - Both produce identical indices: 61,459 terms

DEPENDENCIES:
    External: beautifulsoup4, nltk
    Built-in: os, time, re

DISCLAIMER:
    LLMs were used for logic guidance in SPIMI algorithm implementation.

================================================================================
"""

from Inverted_Index import (
    uncompressed_index,
    validate_queries_on_index,
    print_non_pos_index_size
)

import os
import time
from bs4 import BeautifulSoup
import re


def SPIMI(all_documents):
    """
    Single-Pass In-Memory Indexing: process documents sequentially,
    accumulate term-docID pairs directly into hash table.

    Returns:
        dict: complete inverted index {term: [docIDs]}
    """

    reuters_dir = "reuters21578"
    pair_count = 0

    # Process each .sgm file in order
    for filename in sorted(os.listdir(reuters_dir)):
        if not filename.endswith(".sgm"):
            continue

        filepath = os.path.join(reuters_dir, filename)
        print(f"Processing file: {filename}")

        # Read file with Latin-1 encoding for Reuters special characters
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()

        # Parse XML structure of .sgm file
        soup = BeautifulSoup(content, "html.parser")

        # Extract each document from <reuters> tags
        for reut in soup.find_all("reuters"):
            doc_id = reut.get("newid")
            text_tag = reut.find("text")

            if text_tag:
                # Combine title and body text
                title = text_tag.title.text if text_tag.title else ""
                body = text_tag.body.text if text_tag.body else ""
                doc_text = title + " " + body

                # Tokenize: split on non-alphanumeric (removes punctuation)
                tokens = re.split(r"[^A-Za-z0-9]+", doc_text)

                # SPIMI core: for each token, append docID directly to posting list
                # (traditional approach: collect all pairs first, sort, then build)
                for term in tokens:
                    if term:  # Skip empty strings
                        # Initialize posting list if term is new
                        if term not in all_documents:
                            all_documents[term] = []

                        # Add docID if not already in posting list
                        if doc_id not in all_documents[term]:
                            all_documents[term].append(doc_id)
                            pair_count += 1

        print(f"Finished parsing {filename}.\n")

    print(f"\nSPIMI indexing complete.")
    print(f"Total unique terms: {len(all_documents)}")
    print(f"Total term-docID pairs: {pair_count}")
    return all_documents


if __name__ == "__main__":
    inverted_index = {}
    spimi_index = {}

    # Build naive index
    print("Starting Traditional Index...\n")
    start_trad = time.time()
    inverted_index = uncompressed_index(inverted_index)
    trad_time = time.time() - start_trad
    print(f"Traditional Index built in {trad_time:.2f} seconds\n")

    # Build SPIMI index
    print("Starting SPIMI Index...\n")
    start_spimi = time.time()
    spimi_index = SPIMI(spimi_index)
    spimi_time = time.time() - start_spimi
    print(f"SPIMI Index built in {spimi_time:.2f} seconds\n")

    # Display results
    print(f"Traditional Index: {len(inverted_index)} unique terms")
    print(f"SPIMI Index: {len(spimi_index)} unique terms\n")

    # Performance comparison
    print("===== PERFORMANCE COMPARISON =====")
    print(f"Traditional Time: {trad_time:.2f} seconds")
    print(f"SPIMI Time:      {spimi_time:.2f} seconds")
    print(f"Difference:      {abs(spimi_time - trad_time):.2f} seconds")
    print(f"Ratio:           {max(trad_time, spimi_time) / min(trad_time, spimi_time):.2f}x\n")

    # Validate both produce equivalent results
    validate_queries_on_index(inverted_index, "Traditional Index")
    validate_queries_on_index(spimi_index, "SPIMI Index")

    print_non_pos_index_size(spimi_index, "\nSPIMI Index")