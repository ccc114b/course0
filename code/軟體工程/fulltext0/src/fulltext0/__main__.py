"""CLI entry point for fulltext0."""
import argparse
import sys
import os
from pathlib import Path

import fulltext0

def main():
    parser = argparse.ArgumentParser(prog="fulltext0", description="Full-text search engine")
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="Build index from a text file")
    p_index.add_argument("input", help="Input text file (corpus)")
    p_index.add_argument("-o", "--output", default="_index/data.idx", help="Index output path")
    p_index.add_argument("--offset", default="_index/offsets.bin", help="Offset file path")

    p_query = sub.add_parser("query", help="Query the index")
    p_query.add_argument("keyword", help="Search keyword")
    p_query.add_argument("-i", "--index", default="_index/data.idx", help="Index path")
    p_query.add_argument("--offset", default="_index/offsets.bin", help="Offset file path")
    p_query.add_argument("-c", "--corpus", default="_data/corpus.txt", help="Corpus file for retrieving lines")
    p_query.add_argument("--show", action="store_true", help="Show matching lines")

    args = parser.parse_args()

    if args.command == "index":
        idx_path = args.output.encode("utf-8") if isinstance(args.output, str) else args.output
        off_path = args.offset.encode("utf-8") if isinstance(args.offset, str) else args.offset
        inp = args.input.encode("utf-8") if isinstance(args.input, str) else args.input
        result = fulltext0.build(inp, idx_path, off_path)
        print(f"Index built: {result}")

    elif args.command == "query":
        idx_path = args.index.encode("utf-8") if isinstance(args.index, str) else args.index
        off_path = args.offset.encode("utf-8") if isinstance(args.offset, str) else args.offset
        corpus = args.corpus.encode("utf-8") if isinstance(args.corpus, str) else args.corpus

        with fulltext0.Index(idx_path, off_path) as idx:
            doc_ids = idx.query(args.keyword)
            print(f"Found {len(doc_ids)} results: {doc_ids}")
            if args.show:
                lines = idx.get_lines(corpus, doc_ids)
                for line in lines:
                    print(line)

if __name__ == "__main__":
    main()