# Information Retrieval System 
**Reuters-21578 Corpus | Traditional Indexing vs. SPIMI Comparison**

---

## Quick Start

### Prerequisites
- Python 3.13+
- Libraries: `pip install beautifulsoup4 nltk`
- Reuters corpus folder: `reuters21578/` (21 .sgm files in project directory)

### Run Project
```
python Inverted_Index.py          # Naive indexing demo 
python SPIMI.py                   # SPIMI vs traditional comparison 
```
### Dependencies

**Install external libraries:**
```
pip install beautifulsoup4 nltk
```

**All dependencies:**

External:
- `beautifulsoup4` - HTML/XML parsing
- `nltk` - Porter Stemmer for term reduction

Standard Library (built-in):
- `re` - Regular expressions for tokenization
- `os` - File system operations
- `collections` - defaultdict data structure
- `time` - Performance measurement

Internal:
- `Inverted_Index` module - imported by SPIMI.py
---

## Project Overview

Builds inverted indices on Reuters-21578 corpus (61,459 unique terms) comparing:
- **Traditional indexing**: Collect pairs -> Sort -> Deduplicate -> Build index
- **SPIMI indexing**: Sequential processing with direct hash table accumulation

Tests query functionality (single-term and AND queries) and applies compression techniques (case folding, stemming, stopword removal).

---

## File Structure
```
|── Inverted_Index.py       # Core IR module (indexing, queries, compression)
|── SPIMI.py                # Performance comparison script
|── reuters21578/           # 21 Reuters .sgm corpus files 
└── README.md               # This file
```

---

## What Each Script Does

### Inverted_Index.py
- Parses all 21 Reuters files
- Builds uncompressed index (61,459 terms)
- Tests single-term queries: "copper", "Chrysler", "Bundesbank", "pineapple"
- Tests AND queries: "copper AND pineapple", "Bundesbank AND copper", etc.
- Applies compression pipeline: case folding -> numeric removal -> 30 stopwords -> 150 stopwords -> stemming
- Displays compression impact at each stage
- Final compressed index: 32,307 terms (47.5% reduction)

### SPIMI.py
- Builds traditional index (25.36 seconds)
- Builds SPIMI index (129.34 seconds)
- Compares execution times
- Validates both produce identical 61,459-term indices
- Shows why SPIMI is 5.1x slower (progressive memory degradation)

---

## Key Findings

**Algorithmic Equivalence**
- Both methods produce identical indices, validating correctness

**Performance Difference**
- SPIMI is 5.1x slower due to 1.7M+ individual dictionary operations vs. one batch sort
- Demonstrates memory degradation without block-based processing (processing files progressively slower)

**Query Results**
- Uncompressed: Single-term queries work; AND queries fail (case sensitivity)
- Compressed: Copper gains 42% documents through morphological consolidation, proper nouns (Chrysler, Bundesbank) are lost, rare terms (pineapple) eliminated

**Compression Trade-offs**
- Case folding: -26.1% vocabulary
- Stemming: -25.0% vocabulary  
- Total compression: 47.5% vocabulary reduction
- Benefit: Common term consolidation; Cost: Proper noun precision loss

---

## Expected Results

**Inverted_Index.py Output:**
- Uncompressed index: 61,459 terms
- Compressed index: 32,307 terms
- Query validation showing single-term results and empty AND query results
- Compression statistics table

**SPIMI.py Output:**
- Both indices: 61,459 terms (identical)
- Traditional time: ~25 seconds
- SPIMI time: ~130 seconds
- Performance overhead: +410%
- Progressive file parsing slowdown

---

## Project Details

See `Project_Report.docx` for complete analysis including:
- SPIMI memory management explanation
- Detailed compression effectiveness analysis
- Query processing trade-offs

---

**Author:** Gabriel Asencios (40176253)  
**Dataset:** Reuters-21578
