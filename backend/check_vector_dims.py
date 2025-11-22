"""
Check vector dimensions in database
"""
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://postgres:Fcgdaeb1012345!@db-1.cly4caw06qml.us-west-2.rds.amazonaws.com:5432/audiobot"

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=RealDictCursor)

try:
    # Get vector dimensions
    cursor.execute("""
        SELECT
            id,
            LEFT(summary, 50) as summary,
            array_length(vector::real[], 1) as vector_dims
        FROM articles
        WHERE vector IS NOT NULL
        LIMIT 5
    """)

    rows = cursor.fetchall()

    print(f"Found {len(rows)} articles with vectors:\n")

    for row in rows:
        print(f"Article {row['id']}: {row['vector_dims']} dimensions")
        print(f"  Summary: {row['summary']}")
        print()

    # Try a manual distance calculation
    print("\nAttempting simple vector distance calculation...")

    # Get one vector from the DB
    cursor.execute("SELECT id, vector FROM articles WHERE vector IS NOT NULL LIMIT 1")
    sample = cursor.fetchone()

    if sample:
        print(f"Sample vector from article {sample['id']}:")
        vector_str = sample['vector']
        # Count elements
        elements = vector_str.strip('[]').split(',')
        print(f"  Elements in vector: {len(elements)}")
        print(f"  First 5 elements: {elements[:5]}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    cursor.close()
    conn.close()
