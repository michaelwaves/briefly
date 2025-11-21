# Parallel API Integration

FastAPI service that integrates Parallel Search and Extract APIs with Azure OpenAI embeddings and PostgreSQL storage.

## Features

- **Parallel Search API**: Search the web for relevant articles
- **Parallel Extract API**: Extract detailed content from web pages
- **Azure OpenAI Embeddings**: Generate 1536-dimensional vector embeddings using text-embedding-3-small
- **PostgreSQL + pgvector**: Store articles with vector embeddings for semantic search
- **Batch Processing**: Efficiently process multiple articles in a single request
- **Unified Service**: One-function workflow combining Search → Extract → Embed → Store

## Architecture

```
Parallel Search API → Parallel Extract API → Azure OpenAI → PostgreSQL
     (Find URLs)         (Get Content)      (Embeddings)    (Storage)
```

## Installation

### 1. Install Dependencies

```bash
cd audiobot/backend/parallel_api
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `PARALLEL_API_KEY`: Your Parallel API key
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `DATABASE_URL`: PostgreSQL connection string

### 3. Database Setup

The application automatically creates tables on startup. Ensure your PostgreSQL database has the pgvector extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Usage

### Start the FastAPI Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Unified Service (Recommended)

The easiest way to use the Parallel API integration is through the `ParallelUnifiedService`:

```python
from parallel_unified_service import ParallelUnifiedService

# Initialize
service = ParallelUnifiedService(api_url="http://localhost:8000")

# Search + Extract + Embed + Store in ONE call!
result = service.search_extract_and_store(
    query="Latest AI developments in healthcare",
    max_articles=10,
    category_id=1,
    relevance_score=9
)

print(f"Stored {result['articles_stored']} articles!")
print(f"Article IDs: {result['article_ids']}")
```

### Unified Service Response

```python
{
    "success": True,
    "query": "Latest AI developments in healthcare",
    "articles_found": 15,
    "articles_extracted": 10,
    "articles_stored": 10,
    "article_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "errors": []
}
```

## API Endpoints

### Health Check
```bash
GET /
```

### **NEW**: Generate News Articles with Audio Summaries
```bash
POST /news/generate-with-audio
Content-Type: application/json

{
    "query": "Latest news on AI, Machine Learning, and Startups",
    "max_articles": 10,
    "category_id": null,
    "relevance_score": 9,
    "target_duration_minutes": 2,
    "voice_id": null
}
```

**Complete Workflow**: This endpoint performs the entire pipeline:
1. Searches web using Parallel Search API
2. Extracts full article content using Parallel Extract API
3. Generates 2-minute summaries using Azure OpenAI GPT-4
4. Creates audio files using ElevenLabs text-to-speech
5. Stores articles with embeddings in PostgreSQL

**Response**:
```json
{
    "success": true,
    "query": "Latest news on AI, Machine Learning, and Startups",
    "articles_found": 15,
    "articles_processed": 10,
    "articles_with_audio": 10,
    "articles": [
        {
            "article_id": 17,
            "title": "AI Startup Raises $50M...",
            "source": "https://example.com/article",
            "audio_filename": "article_1_20251121_153000.mp3",
            "audio_path": "/path/to/generated_audio/article_1_20251121_153000.mp3",
            "summary_word_count": 295
        }
    ],
    "errors": []
}
```

### Create Single Article
```bash
POST /articles/
Content-Type: application/json

{
    "text": "Article content...",
    "summary": "Article summary",
    "relevance_score": 8,
    "source": "https://example.com",
    "category_id": 1
}
```

### Batch Process Parallel Extract Results
```bash
POST /articles/batch/
Content-Type: application/json

{
    "results": [
        {
            "url": "https://example.com/article",
            "title": "Article Title",
            "excerpts": ["Excerpt text..."],
            "publish_date": "2025-11-21T00:00:00Z"
        }
    ],
    "default_category_id": 1,
    "default_relevance_score": 8
}
```

### Get Articles
```bash
GET /articles/?skip=0&limit=100
```

### Get Single Article
```bash
GET /articles/{article_id}
```

### Delete Article
```bash
DELETE /articles/{article_id}
```

## Database Schema

### Articles Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `text` | TEXT | Article content (from Parallel excerpt) |
| `summary` | TEXT | Article title/summary |
| `relevance_score` | INTEGER | Relevance score (1-10) |
| `date_written` | TIMESTAMP | Article publish date |
| `date_created` | TIMESTAMP | Record creation timestamp |
| `source` | TEXT | Source URL |
| `category_id` | INTEGER | Foreign key to categories |
| `vector` | VECTOR(1536) | Embedding vector from Azure OpenAI |

### Categories Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `name` | STRING | Category name (unique) |
| `description` | TEXT | Category description |

## Data Flow

1. **Search**: Parallel Search API finds relevant articles
2. **Extract**: Parallel Extract API retrieves full content and excerpts
3. **Embed**: Azure OpenAI generates 1536-dimensional embeddings from excerpts
4. **Store**: PostgreSQL stores both text and vector embeddings

### Excerpt Mapping

- `result.excerpts[0]` → `article.text` (raw text)
- `result.excerpts[0]` → Azure OpenAI → `article.vector` (1536-dim embedding)

Both `text` and `vector` fields contain the same content - one as raw text, one as vector embedding.

## Example Workflow

```python
from parallel import Parallel
import requests

# 1. Search with Parallel
parallel = Parallel(api_key="your_key")
search = parallel.beta.search(
    objective="Find AI articles",
    search_queries=["artificial intelligence news"],
    max_results=10
)

# 2. Extract content
urls = [r.url for r in search.results]
extract = parallel.beta.extract(
    urls=urls,
    objective="Extract article content",
    excerpts={"max_chars_per_result": 50000},
    full_content=True
)

# 3. Send to FastAPI for embedding and storage
response = requests.post(
    "http://localhost:8000/articles/batch/",
    json={
        "results": [
            {
                "url": r.url,
                "title": r.title,
                "excerpts": r.excerpts,
                "full_content": r.full_content,
                "publish_date": r.publish_date
            }
            for r in extract.results
        ],
        "default_relevance_score": 8
    }
)

print(response.json())
```

## Error Handling

The API handles errors gracefully:

- **No content**: Skips articles without excerpts or content
- **Invalid dates**: Logs warning and continues
- **Embedding failures**: Logs error but doesn't fail entire batch
- **Database errors**: Rolls back transaction and returns detailed error

## Logging

All operations are logged with INFO level. Check logs for:
- Article processing status
- Embedding generation
- Database operations
- Error details

## Performance Considerations

- **Batch processing**: Process multiple articles in single transaction
- **Connection pooling**: SQLAlchemy engine with pool_pre_ping
- **Embedding caching**: Singleton EmbeddingService instance
- **Text truncation**: Automatically truncates long text to fit token limits

## Development

### Run Tests

```bash
python -m pytest
```

### Code Structure

```
parallel_api/
├── __init__.py                     # Package initialization
├── main.py                         # FastAPI application
├── database.py                     # Database connection
├── models.py                       # SQLAlchemy models
├── schemas.py                      # Pydantic schemas
├── embedding_service.py            # Azure OpenAI embeddings
├── parallel_unified_service.py     # Unified Search+Extract service
├── requirements.txt                # Dependencies
├── .env.example                    # Environment template
└── README.md                       # This file
```

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.
