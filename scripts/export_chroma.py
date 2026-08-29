"""Dumps everything in a ChromaDB collection to a JSON file - chunk ids,
text, and metadata for every stored chunk. Embeddings are excluded by
default (384 floats x every chunk gets large fast); pass --embeddings
to include them.

There's no single-file export like `pg_dump` for Chroma - this is the
closest equivalent, built on the same HttpClient used everywhere else
in this project (see app/services/vector_store.py).

Usage (from the repo root, with the Docker Compose stack up):
    python3 scripts/export_chroma.py
    python3 scripts/export_chroma.py --collection documents --out my_export.json
    python3 scripts/export_chroma.py --embeddings
"""

import argparse
import json
import os

import chromadb

# Deliberately not importing app.core.config here - see inspect_chroma.py
# for why (sys.path doesn't include the repo root when run this way).


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
        help="Collection name to export (default: documents)",
    )
    parser.add_argument(
        "--out",
        default="chroma_export.json",
        help="Output file path (default: chroma_export.json)",
    )
    parser.add_argument(
        "--embeddings",
        action="store_true",
        help="Include raw embedding vectors in the export (large)",
    )
    args = parser.parse_args()

    client = chromadb.HttpClient(host=args.host, port=args.port)
    col = client.get_collection(args.collection)

    include = ["metadatas", "documents"]
    if args.embeddings:
        include.append("embeddings")

    data = col.get(include=include)

    # get() always returns ids; convert any non-JSON-native types
    # (embeddings come back as numpy-backed lists via the client) so
    # json.dump doesn't choke on them.
    export = {
        "collection": args.collection,
        "count": len(data["ids"]),
        "ids": data["ids"],
        "documents": data["documents"],
        "metadatas": data["metadatas"],
    }
    if args.embeddings:
        export["embeddings"] = [list(map(float, v)) for v in data["embeddings"]]

    with open(args.out, "w") as f:
        json.dump(export, f, indent=2)

    print(f"Exported {export['count']} chunks from '{args.collection}' to {args.out}")


if __name__ == "__main__":
    main()
