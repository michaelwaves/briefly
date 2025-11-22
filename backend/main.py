from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os

from models import (
    ArticleResponse,
    GeneratePodcastRequest,
    GeneratePodcastFromArticlesRequest,
    GeneratePodcastFromCategoriesRequest,
    GenerateAudioFromTextRequest,
    SearchArticlesRequest,
    PodcastResponse,
    VoicesResponse,
    VoiceInfo
)
from services.article_service import ArticleService
from services.tts_service import tts_service
from services.s3_service import s3_service
from services.podcast_service import podcast_service
from config import settings

app = FastAPI(
    title="Audiobot API",
    description="Text-to-speech API for generating podcasts from articles using ElevenLabs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Audiobot API",
        "version": "1.0.0"
    }


@app.get("/voices", response_model=VoicesResponse)
async def get_voices():
    """Get list of available ElevenLabs voices."""
    try:
        voices = tts_service.get_available_voices()
        return VoicesResponse(
            voices=[VoiceInfo(**voice) for voice in voices]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch voices: {str(e)}"
        )


@app.post("/articles/search", response_model=List[ArticleResponse])
async def search_articles(request: SearchArticlesRequest):
    """Search articles using vector similarity."""
    try:
        articles = ArticleService.search_articles_by_text(
            query_text=request.query,
            limit=request.limit,
            category_ids=request.category_ids
        )
        return [ArticleResponse(**article) for article in articles]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search articles: {str(e)}"
        )


@app.get("/articles/user/{user_id}", response_model=List[ArticleResponse])
async def get_user_articles(
    user_id: int,
    limit: int = 10,
    similarity_threshold: float = 0.7
):
    """Get articles based on user preferences."""
    try:
        articles = ArticleService.get_articles_by_user_preferences(
            user_id=user_id,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        return [ArticleResponse(**article) for article in articles]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user articles: {str(e)}"
        )


@app.get("/articles/category", response_model=List[ArticleResponse])
async def get_articles_by_category(
    category_ids: List[int],
    limit: int = 10
):
    """Get articles by category IDs."""
    try:
        articles = ArticleService.get_articles_by_category(
            category_ids=category_ids,
            limit=limit
        )
        return [ArticleResponse(**article) for article in articles]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch articles: {str(e)}"
        )


@app.post("/podcast/generate/user", response_model=PodcastResponse)
async def generate_podcast_from_user_preferences(request: GeneratePodcastRequest):
    """Generate a podcast based on user preferences."""
    try:
        # Fetch articles based on user preferences
        articles = ArticleService.get_articles_by_user_preferences(
            user_id=request.user_id,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )

        if not articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles found matching user preferences"
            )

        # Generate audio from articles
        audio_path, script = tts_service.generate_audio_from_articles(
            articles=articles,
            voice_id=request.voice_id
        )

        # Upload to S3
        s3_url = s3_service.upload_podcast(audio_path)

        # Save podcast record to database
        podcast_id = podcast_service.create_podcast_record(
            user_id=request.user_id,
            script=script,
            s3_link=s3_url
        )

        # Clean up local file
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return PodcastResponse(
            success=True,
            audio_path=s3_url,
            filename=os.path.basename(s3_url),
            article_count=len(articles),
            message=f"Successfully generated podcast with {len(articles)} articles"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate podcast: {str(e)}"
        )


@app.post("/podcast/generate/articles", response_model=PodcastResponse)
async def generate_podcast_from_articles(request: GeneratePodcastFromArticlesRequest):
    """Generate a podcast from specific article IDs."""
    try:
        # Fetch articles by IDs
        articles = ArticleService.get_articles_by_ids(
            article_ids=request.article_ids
        )

        if not articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles found with provided IDs"
            )

        # Generate audio from articles
        audio_path, script = tts_service.generate_audio_from_articles(
            articles=articles,
            voice_id=request.voice_id
        )

        return PodcastResponse(
            success=True,
            audio_path=audio_path,
            filename=os.path.basename(audio_path),
            article_count=len(articles),
            message=f"Successfully generated podcast with {len(articles)} articles"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate podcast: {str(e)}"
        )


@app.post("/podcast/generate/categories", response_model=PodcastResponse)
async def generate_podcast_from_categories(request: GeneratePodcastFromCategoriesRequest):
    """Generate a podcast from articles in specific categories."""
    try:
        # Fetch articles by categories
        articles = ArticleService.get_articles_by_category(
            category_ids=request.category_ids,
            limit=request.limit
        )

        if not articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles found in provided categories"
            )

        # Generate audio from articles
        audio_path, script = tts_service.generate_audio_from_articles(
            articles=articles,
            voice_id=request.voice_id
        )

        return PodcastResponse(
            success=True,
            audio_path=audio_path,
            filename=os.path.basename(audio_path),
            article_count=len(articles),
            message=f"Successfully generated podcast with {len(articles)} articles"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate podcast: {str(e)}"
        )


@app.post("/audio/generate", response_model=PodcastResponse)
async def generate_audio_from_text(request: GenerateAudioFromTextRequest):
    """Generate audio from raw text."""
    try:
        audio_path = tts_service.generate_audio_from_text(
            text=request.text,
            filename=request.filename,
            voice_id=request.voice_id
        )

        return PodcastResponse(
            success=True,
            audio_path=audio_path,
            filename=os.path.basename(audio_path),
            article_count=0,
            message="Successfully generated audio from text"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audio: {str(e)}"
        )


@app.get("/audio/download/{filename}")
async def download_audio(filename: str):
    """Download generated audio file."""
    file_path = os.path.join("generated_audio", filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename
    )


def main():
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )


if __name__ == "__main__":
    main()
