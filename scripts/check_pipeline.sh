#!/bin/sh
# Inspects the most recently uploaded document across every stage of the
# processing pipeline: DB row, chunks, embeddings, and the worker's log
# for that document. Run from the repo root with the Docker Compose
# stack up (docker compose up -d).
#
# uploads/chunks/embeddings live inside named Docker volumes, not on the
# host filesystem, hence `docker compose exec` rather than a plain `cat`.
#
# Usage: ./scripts/check_pipeline.sh

set -e

ID=$(docker compose exec -T db psql -U rag_user -d rag_chatbot -t -c "SELECT id FROM documents ORDER BY id DESC LIMIT 1;" | tr -d ' ')

if [ -z "$ID" ]; then
    echo "No documents found - upload one first."
    exit 1
fi

echo "=== Latest document id: $ID ==="
echo ""

echo "--- DB row ---"
docker compose exec -T db psql -U rag_user -d rag_chatbot -c "SELECT id, filename, status, error_message FROM documents WHERE id = $ID;"

echo "--- Chunks ---"
docker compose exec -T app sh -c "cat chunks/$ID.json 2>/dev/null || echo 'NOT FOUND - check status above (still pending/processing?)'"
echo ""

echo "--- Embeddings (truncated) ---"
docker compose exec -T app sh -c "cat embeddings/$ID.json 2>/dev/null | head -c 300 || echo 'NOT FOUND'"
echo ""
echo ""

echo "--- Worker log for this document ---"
docker compose logs worker 2>&1 | grep -A 3 "document_id=$ID "
