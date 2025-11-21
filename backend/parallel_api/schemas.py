"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class ParallelExtractResult(BaseModel):
    """Schema for a single Parallel Extract API result"""
    url: str
    title: Optional[str] = None
    excerpts: Optional[List[str]] = []
    full_content: Optional[str] = None
    publish_date: Optional[str] = None
    status: Optional[str] = None


class ArticleCreate(BaseModel):
    """Schema for creating an article"""
    text: str = Field(..., description="Main text content (from Parallel excerpt)")
    summary: Optional[str] = Field(None, description="Summary of the article")
    relevance_score: Optional[int] = Field(None, ge=1, le=10, description="Relevance score 1-10")
    date_written: Optional[datetime] = Field(None, description="Date the article was written")
    source: Optional[str] = Field(None, description="Source URL or publication name")
    category_id: Optional[int] = Field(None, description="Category ID reference")


class ArticleResponse(BaseModel):
    """Schema for article response"""
    id: int
    text: str
    summary: Optional[str]
    relevance_score: Optional[int]
    date_written: Optional[datetime]
    date_created: datetime
    source: Optional[str]
    category_id: Optional[int]

    class Config:
        from_attributes = True


class ParallelExtractBatch(BaseModel):
    """Schema for batch processing Parallel Extract results"""
    results: List[ParallelExtractResult]
    default_category_id: Optional[int] = Field(None, description="Default category for all articles")
    default_relevance_score: Optional[int] = Field(5, ge=1, le=10, description="Default relevance score")


class BatchProcessResponse(BaseModel):
    """Response for batch processing"""
    success: bool
    articles_created: int
    article_ids: List[int]
    errors: List[str] = []


class ArticleAudioInfo(BaseModel):
    """Information about an article and its generated audio"""
    article_id: int
    title: str
    source: str
    audio_filename: str
    audio_path: str
    summary_word_count: int


class NewsWithAudioRequest(BaseModel):
    """Request for generating news articles with audio summaries"""
    query: str = Field(..., description="Search query for news articles")
    max_articles: int = Field(10, ge=1, le=20, description="Maximum articles to process")
    category_id: Optional[int] = Field(None, description="Optional category ID")
    relevance_score: int = Field(8, ge=1, le=10, description="Relevance score")
    target_duration_minutes: int = Field(2, ge=1, le=5, description="Target audio duration per article")
    voice_id: Optional[str] = Field(None, description="Optional ElevenLabs voice ID")


class NewsWithAudioResponse(BaseModel):
    """Response for news articles with audio summaries"""
    success: bool
    query: str
    articles_found: int
    articles_processed: int
    articles_with_audio: int
    articles: List[ArticleAudioInfo]
    errors: List[str] = []
