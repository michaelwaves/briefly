"""
Summarization service using Azure OpenAI
Creates concise summaries optimized for text-to-speech (2-minute audio)
"""
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import logging
from typing import Optional

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SummarizationService:
    """Service to generate summaries using Azure OpenAI"""

    def __init__(self):
        """Initialize Azure OpenAI client"""
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        # Use GPT-4 or GPT-3.5 for summarization
        self.model = os.getenv(
            "AZURE_OPENAI_CHAT_DEPLOYMENT",
            "gpt-4"  # Fallback to gpt-4
        )

        logger.info(f"Initialized SummarizationService with model: {self.model}")

    def create_audio_summary(
        self,
        text: str,
        title: str = "",
        target_duration_minutes: int = 2
    ) -> Optional[str]:
        """
        Create a summary optimized for 2-minute audio narration

        Approximate words per minute for speech: 150 WPM
        For 2 minutes: ~300 words

        Args:
            text: Full article text to summarize
            title: Article title (optional, for context)
            target_duration_minutes: Target duration in minutes (default: 2)

        Returns:
            Summary text optimized for audio narration, or None if error
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for summarization")
            return None

        try:
            # Calculate target word count (150 words per minute)
            target_words = target_duration_minutes * 150

            # Create the summarization prompt
            system_prompt = (
                "You are an expert news summarizer creating content for audio podcasts. "
                "Create engaging, natural-sounding summaries that work well when read aloud. "
                "Use clear, conversational language. Avoid complex formatting or special characters."
            )

            user_prompt = (
                f"Summarize the following article in approximately {target_words} words "
                f"(for a {target_duration_minutes}-minute audio narration at 150 words per minute).\n\n"
                "Requirements:\n"
                "- Make it engaging and natural for audio listening\n"
                "- Use conversational language\n"
                "- Include key facts and insights\n"
                "- Start with a brief hook\n"
                "- End with a conclusion or key takeaway\n"
                "- Avoid bullet points, use flowing prose\n\n"
            )

            if title:
                user_prompt += f"Article Title: {title}\n\n"

            user_prompt += f"Article Text:\n{text[:8000]}"  # Limit input to prevent token overflow

            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500  # ~300-400 words
            )

            summary = response.choices[0].message.content.strip()

            # Log word count
            word_count = len(summary.split())
            logger.info(f"Generated summary with {word_count} words (target: {target_words})")

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return None

    def create_batch_summaries(
        self,
        articles: list[dict],
        target_duration_minutes: int = 2
    ) -> list[Optional[str]]:
        """
        Create summaries for multiple articles

        Args:
            articles: List of article dicts with 'text' and optionally 'title'
            target_duration_minutes: Target duration per summary

        Returns:
            List of summaries (or None for failed items)
        """
        summaries = []

        for idx, article in enumerate(articles):
            try:
                text = article.get('text', '')
                title = article.get('title') or article.get('summary', '')

                summary = self.create_audio_summary(
                    text=text,
                    title=title,
                    target_duration_minutes=target_duration_minutes
                )

                summaries.append(summary)
                logger.info(f"Generated summary {idx+1}/{len(articles)}")

            except Exception as e:
                logger.error(f"Error generating summary for article {idx}: {str(e)}")
                summaries.append(None)

        return summaries


# Global singleton instance
_summarization_service = None


def get_summarization_service() -> SummarizationService:
    """
    Get or create summarization service singleton

    Returns:
        SummarizationService instance
    """
    global _summarization_service

    if _summarization_service is None:
        _summarization_service = SummarizationService()

    return _summarization_service
