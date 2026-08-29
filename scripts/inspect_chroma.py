"""Prints what's actually stored in ChromaDB - collections, chunk count,
and a sample of chunks with their text and metadata.

Chroma has no SQL shell; the HttpClient is the supported way to look at
its data (see docs/sprints/06-vector-database-chromadb.md for why it
runs as its own server rather than an embedded/file-based client).

Usage (from the repo root, with the Docker Compose stack up):
    python3 scripts/inspect_chroma.py
    python3 scripts/inspect_chroma.py --limit 20
    python3 scripts/inspect_chroma.py --collection documents --embeddings
"""

import argparse
import os

import chromadb

# Deliberately not importing app.core.config here: running `python3
# scripts/inspect_chroma.py` puts scripts/ (not the repo root) on
# sys.path, so `from app... import` fails unless PYTHONPATH is set up
# first. Reading CHROMA_HOST/CHROMA_PORT directly keeps this a
# standalone utility that only needs `pip install chromadb` to run.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host",
        default=os.environ.get("CHROMA_HOST", "localhost"),
        help="Chroma server host (default: localhost, or $CHROMA_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("CHROMA_PORT", "8001")),
        help="Chroma server port (default: 8001, or $CHROMA_PORT)",
    )
    parser.add_argument(
        "--collection",
        default="documents",
        help="Collection name to inspect (default: documents)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="How many chunks to show (default: 10)",
    )
    parser.add_argument(
        "--embeddings",
        action="store_true",
        help="Also print the raw embedding vectors (384 floats each - verbose)",
    )
    args = parser.parse_args()

    client = chromadb.HttpClient(host=args.host, port=args.port)

    collections = client.list_collections()
    print(f"Collections: {[c.name for c in collections]}")

    if not any(c.name == args.collection for c in collections):
        print(f"Collection '{args.collection}' not found.")
        return

    col = client.get_collection(args.collection)
    print(f"Total chunks in '{args.collection}': {col.count()}")
    print()

    include = ["metadatas", "documents"]
    if args.embeddings:
        include.append("embeddings")

    data = col.get(limit=args.limit, include=include)

    for i, doc in enumerate(data["documents"]):
        print("---")
        print("id:", data["ids"][i])
        print("metadata:", data["metadatas"][i])
        print("text:", doc[:200] + ("..." if len(doc) > 200 else ""))
        if args.embeddings:
            vector = data["embeddings"][i]
            print(f"embedding: [{vector[0]:.4f}, {vector[1]:.4f}, ... ] ({len(vector)} dims)")


if __name__ == "__main__":
    main()
