"""
Vector similarity search for articles in the database

This script performs semantic search using pgvector and Azure OpenAI embeddings.
Works around PostgreSQL ORDER BY issues with pgvector by sorting results in Python.

Usage:
    python vector_search.py "Your search query here"
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

# Add parallel_api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'parallel_api'))

from parallel_api.embedding_service import get_embedding_service

# Database connection
DATABASE_URL = "postgresql://postgres:Fcgdaeb1012345!@db-1.cly4caw06qml.us-west-2.rds.amazonaws.com:5432/audiobot"


def search_by_vector_similarity(query: str, top_k: int = 10):
    """
    Search articles using vector similarity

    Args:
        query: Search query text
        top_k: Number of results to return (default: 10)

    Returns:
        List of articles sorted by similarity (lower distance = more similar)
    """
    print(f"🔍 Searching for: '{query}'")
    print(f"📊 Returning top {top_k} results\n")

    # Generate embedding for the query
    print("Generating embedding for query...")
    embedding_service = get_embedding_service()
    query_embedding = embedding_service.generate_embedding(query)

    if not query_embedding:
        print("❌ Failed to generate embedding")
        return []

    print(f"✓ Generated embedding with {len(query_embedding)} dimensions\n")

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Fetch all articles with distance calculations
        # Note: We don't use ORDER BY here due to pgvector issues with PostgreSQL query planner
        # Instead, we fetch all results and sort in Python
        cursor.execute("""
            SELECT
                id,
                summary,
                LEFT(text, 200) as text_preview,
                source,
                relevance_score,
                date_written,
                date_created,
                (vector <=> %s::vector) as distance
            FROM articles
        """, (query_embedding,))

        rows = cursor.fetchall()

        if not rows:
            print("❌ No articles found in database")
            return []

        # Sort by distance in Python (lower distance = more similar)
        rows_sorted = sorted(rows, key=lambda x: x['distance'])[:top_k]

        print(f"✓ Found {len(rows_sorted)} results:\n")
        print("=" * 100)

        for idx, row in enumerate(rows_sorted, 1):
            print(f"\n{idx}. Article ID: {row['id']}")
            print(f"   Distance: {row['distance']:.4f} (lower = more similar)")
            print(f"   Similarity: {(1 - row['distance']):.2%}")
            print(f"   Summary: {row['summary'] or 'No summary'}")
            print(f"   Text Preview: {row['text_preview']}...")
            print(f"   Source: {row['source'] or 'No source'}")
            print(f"   Relevance Score: {row['relevance_score'] or 'N/A'}")
            print(f"   Date Written: {row['date_written'] or 'Unknown'}")
            print(f"   Date Created: {row['date_created']}")
            print("-" * 100)

        return rows_sorted

    except Exception as e:
        print(f"❌ Error searching database: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Get query from command line or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "News about AI"

    search_by_vector_similarity(query, top_k=10)
