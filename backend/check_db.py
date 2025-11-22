"""
Check database contents
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:Fcgdaeb1012345!@db-1.cly4caw06qml.us-west-2.rds.amazonaws.com:5432/audiobot"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check total articles
    result = conn.execute(text("SELECT COUNT(*) FROM articles"))
    total = result.scalar()
    print(f"Total articles in database: {total}")

    # Check articles with vectors
    result = conn.execute(text("SELECT COUNT(*) FROM articles WHERE vector IS NOT NULL"))
    with_vectors = result.scalar()
    print(f"Articles with vectors: {with_vectors}")

    # Check articles without vectors
    result = conn.execute(text("SELECT COUNT(*) FROM articles WHERE vector IS NULL"))
    without_vectors = result.scalar()
    print(f"Articles without vectors: {without_vectors}")

    # Sample some articles
    if total > 0:
        print("\nSample articles:")
        result = conn.execute(text("""
            SELECT id, LEFT(summary, 100) as summary, source,
                   CASE WHEN vector IS NOT NULL THEN 'Yes' ELSE 'No' END as has_vector
            FROM articles
            LIMIT 5
        """))
        for row in result:
            print(f"  ID {row.id}: {row.summary} (Vector: {row.has_vector})")
