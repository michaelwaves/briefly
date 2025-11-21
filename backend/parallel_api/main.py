"""
FastAPI application for processing Parallel Extract API results and storing in PostgreSQL
"""
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging
import os
import sys

# Add parent directory to path to import from backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import get_db, engine
from models import Base, Article
from schemas import (
    ArticleCreate,
    ArticleResponse,
    ParallelExtractBatch,
    BatchProcessResponse,
    ParallelExtractResult,
    NewsWithAudioRequest,
    NewsWithAudioResponse,
    ArticleAudioInfo
)
from embedding_service import get_embedding_service
from summarization_service import get_summarization_service
from parallel_unified_service import ParallelUnifiedService

# Import TTS service from backend
try:
    from services.tts_service import tts_service
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Could not import tts_service from backend. Audio generation will not be available.")
    tts_service = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Parallel Extract to Database API",
    description="API to process Parallel Extract results and store them in PostgreSQL",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Create tables on startup if they don't exist"""
    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Parallel Extract to Database API is running",
        "version": "1.0.0"
    }


@app.post("/articles/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(article: ArticleCreate, db: Session = Depends(get_db)):
    """
    Create a single article with embedding
    """
    try:
        # Generate embedding for the text
        embedding_service = get_embedding_service()
        embedding = embedding_service.generate_embedding(article.text)

        # Create article with embedding
        article_dict = article.model_dump()
        article_dict['vector'] = embedding

        db_article = Article(**article_dict)
        db.add(db_article)
        db.commit()
        db.refresh(db_article)

        logger.info(f"Created article with ID: {db_article.id} (embedding: {len(embedding) if embedding else 0} dims)")
        return db_article

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating article: {str(e)}"
        )


@app.post("/articles/batch/", response_model=BatchProcessResponse)
async def process_parallel_extract_batch(
    batch: ParallelExtractBatch,
    db: Session = Depends(get_db)
):
    """
    Process a batch of Parallel Extract API results and create articles

    This endpoint takes the output from Parallel Extract API and maps:
    - excerpts[0] -> article.text (main content)
    - url -> article.source
    - publish_date -> article.date_written
    """
    created_articles = []
    article_ids = []
    errors = []

    try:
        for idx, result in enumerate(batch.results):
            try:
                # Extract the first excerpt as the main text
                # Parallel returns excerpts as a list, we'll use the first one
                text_content = None

                if result.excerpts and len(result.excerpts) > 0:
                    text_content = result.excerpts[0]
                elif result.full_content:
                    # If no excerpts, use full_content (truncate if too long)
                    text_content = result.full_content[:10000]  # Limit to 10k chars
                else:
                    errors.append(f"Result {idx}: No text content available")
                    continue

                # Parse publish_date if available
                date_written = None
                if result.publish_date:
                    try:
                        date_written = datetime.fromisoformat(result.publish_date.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"Could not parse date {result.publish_date}: {e}")

                # Generate embedding for the text
                embedding_service = get_embedding_service()
                embedding = embedding_service.generate_embedding(text_content)

                # Create article with embedding
                article = Article(
                    text=text_content,
                    summary=result.title,  # Use title as summary
                    relevance_score=batch.default_relevance_score,
                    date_written=date_written,
                    source=result.url,
                    category_id=batch.default_category_id,
                    vector=embedding
                )

                db.add(article)
                db.flush()  # Flush to get the ID

                created_articles.append(article)
                article_ids.append(article.id)

                logger.info(f"Prepared article {article.id} from {result.url}")

            except Exception as e:
                error_msg = f"Result {idx} ({result.url if hasattr(result, 'url') else 'unknown'}): {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Commit all articles
        db.commit()

        logger.info(f"Successfully created {len(created_articles)} articles")

        return BatchProcessResponse(
            success=len(created_articles) > 0,
            articles_created=len(created_articles),
            article_ids=article_ids,
            errors=errors
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Batch processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )


@app.get("/articles/", response_model=List[ArticleResponse])
async def get_articles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all articles with pagination
    """
    articles = db.query(Article).offset(skip).limit(limit).all()
    return articles


@app.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """
    Get a single article by ID
    """
    article = db.query(Article).filter(Article.id == article_id).first()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )

    return article


@app.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: int, db: Session = Depends(get_db)):
    """
    Delete an article by ID
    """
    article = db.query(Article).filter(Article.id == article_id).first()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )

    db.delete(article)
    db.commit()

    logger.info(f"Deleted article with ID: {article_id}")
    return None


@app.post("/news/generate-with-audio", response_model=NewsWithAudioResponse)
async def generate_news_with_audio(request: NewsWithAudioRequest, db: Session = Depends(get_db)):
    """
    Complete workflow: Search → Extract → Summarize → Generate Audio → Store

    This endpoint:
    1. Uses Parallel Search API to find relevant articles
    2. Uses Parallel Extract API to get full content
    3. Uses Azure OpenAI to create 2-minute summaries
    4. Uses ElevenLabs to generate audio for each summary
    5. Stores articles with embeddings in the database

    Returns article metadata and paths to generated audio files
    """
    if not tts_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Text-to-speech service is not available"
        )

    logger.info(f"Starting news with audio generation for query: '{request.query}'")

    response_data = {
        "success": False,
        "query": request.query,
        "articles_found": 0,
        "articles_processed": 0,
        "articles_with_audio": 0,
        "articles": [],
        "errors": []
    }

    try:
        # Step 1 & 2: Search and Extract using Parallel API
        logger.info("Step 1-2: Searching and extracting articles with Parallel API...")

        parallel_service = ParallelUnifiedService(api_url="http://localhost:8000")

        # For AI/ML/Startup news, we'll use the query with additional search queries
        search_queries = [
            request.query,
            "AI artificial intelligence",
            "machine learning ML",
            "startups technology",
            "agentic AI systems",
            "MCP model context protocol",
            "HITL human in the loop",
            "reinforcement learning RL"
        ]

        from parallel import Parallel
        parallel_client = Parallel(api_key=os.environ.get("PARALLEL_API_KEY"))

        # Search
        search_result = parallel_client.beta.search(
            objective=request.query,
            search_queries=search_queries[:4],  # Limit to 4 queries
            max_results=request.max_articles,
            excerpts={"max_chars_per_result": 8000}
        )

        response_data["articles_found"] = len(search_result.results)
        logger.info(f"✓ Found {response_data['articles_found']} articles")

        if not search_result.results:
            response_data["errors"].append("No articles found")
            return NewsWithAudioResponse(**response_data)

        # Extract
        urls = [r.url for r in search_result.results][:request.max_articles]
        extract_result = parallel_client.beta.extract(
            urls=urls,
            objective=f"Extract detailed content for: {request.query}",
            excerpts={"max_chars_per_result": 50000},
            full_content=True
        )

        logger.info(f"✓ Extracted {len(extract_result.results)} articles")

        if not extract_result.results:
            response_data["errors"].append("No content extracted")
            return NewsWithAudioResponse(**response_data)

        # Step 3-5: Process each article (Summarize → Audio → Store)
        summarization_service = get_summarization_service()
        embedding_service = get_embedding_service()

        output_dir = os.path.join(os.path.dirname(__file__), "..", "generated_audio")
        os.makedirs(output_dir, exist_ok=True)

        for idx, result in enumerate(extract_result.results):
            try:
                # Get full text
                text_content = None
                if result.excerpts and len(result.excerpts) > 0:
                    text_content = result.excerpts[0]
                elif result.full_content:
                    text_content = result.full_content[:10000]
                else:
                    response_data["errors"].append(f"Article {idx}: No text content")
                    continue

                # Step 3: Generate 2-minute summary using Azure OpenAI
                logger.info(f"Generating {request.target_duration_minutes}-minute summary for article {idx+1}...")
                summary_text = summarization_service.create_audio_summary(
                    text=text_content,
                    title=result.title or "",
                    target_duration_minutes=request.target_duration_minutes
                )

                if not summary_text:
                    response_data["errors"].append(f"Article {idx}: Failed to generate summary")
                    continue

                word_count = len(summary_text.split())
                logger.info(f"✓ Generated summary with {word_count} words")

                # Step 4: Generate audio from summary using ElevenLabs
                logger.info(f"Generating audio for article {idx+1}...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_filename = f"article_{idx+1}_{timestamp}.mp3"

                audio_path = tts_service.generate_audio_from_text(
                    text=summary_text,
                    output_dir=output_dir,
                    filename=audio_filename,
                    voice_id=request.voice_id
                )

                logger.info(f"✓ Generated audio: {audio_filename}")

                # Step 5: Store article in database with embedding
                logger.info(f"Storing article {idx+1} in database...")

                # Parse publish date
                date_written = None
                if result.publish_date:
                    try:
                        date_written = datetime.fromisoformat(result.publish_date.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"Could not parse date: {e}")

                # Generate embedding from original text (not summary)
                embedding = embedding_service.generate_embedding(text_content)

                # Create article
                article = Article(
                    text=text_content,  # Store full text
                    summary=summary_text,  # Store the 2-minute summary
                    relevance_score=request.relevance_score,
                    date_written=date_written,
                    source=result.url,  # URL stored in source field
                    category_id=request.category_id,
                    vector=embedding
                )

                db.add(article)
                db.flush()

                logger.info(f"✓ Stored article {article.id} from {result.url}")

                # Add to response
                response_data["articles"].append({
                    "article_id": article.id,
                    "title": result.title or "Untitled",
                    "source": result.url,
                    "audio_filename": audio_filename,
                    "audio_path": audio_path,
                    "summary_word_count": word_count
                })

                response_data["articles_with_audio"] += 1
                response_data["articles_processed"] += 1

            except Exception as e:
                error_msg = f"Article {idx} ({result.url if hasattr(result, 'url') else 'unknown'}): {str(e)}"
                response_data["errors"].append(error_msg)
                logger.error(error_msg)

        # Commit all articles
        db.commit()

        response_data["success"] = response_data["articles_with_audio"] > 0

        logger.info(f"✓ Complete! Processed {response_data['articles_with_audio']} articles with audio")

        return NewsWithAudioResponse(**response_data)

    except Exception as e:
        db.rollback()
        error_msg = f"Workflow error: {str(e)}"
        response_data["errors"].append(error_msg)
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
