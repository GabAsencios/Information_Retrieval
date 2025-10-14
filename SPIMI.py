import Inverted_Index as ii
import os

def SPIMI(filepath):

    ii.parse_sgm_file(filepath)


if __name__ == "__main__":

    # Global inverted index
    all_documents = {}

    print("Parsing all Reuters .sgm files...\n")

    ii.process_all()

    print("\nFinished parsing all files.")
    print(f"Total unique words indexed: {len(all_documents)}\n")