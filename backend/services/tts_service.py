from typing import List, Dict, Any, Optional, Tuple
from elevenlabs import ElevenLabs, save
from config import settings
import os
from datetime import datetime


class TTSService:
    """Service for text-to-speech conversion using ElevenLabs API."""

    def __init__(self):
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.voice_id = settings.elevenlabs_voice_id

    def generate_audio_from_articles(
        self,
        articles: List[Dict[str, Any]],
        output_dir: str = "generated_audio",
        voice_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate audio from a list of articles and combine them into a podcast-style audio.

        Args:
            articles: List of article dictionaries with 'text' or 'summary' fields
            output_dir: Directory to save the generated audio file
            voice_id: Optional custom voice ID (uses default if not provided)

        Returns:
            Tuple of (audio file path, script text)
        """
        # Use provided voice_id or fall back to default
        voice = voice_id or self.voice_id

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Combine article content into a script
        script = self._create_podcast_script(articles)

        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"podcast_{timestamp}.mp3"
        output_path = os.path.join(output_dir, output_filename)

        # Generate audio using ElevenLabs
        audio = self.client.text_to_speech.convert(
            voice_id=voice,
            text=script,
            model_id="eleven_multilingual_v2"
        )

        # Save the audio file
        with open(output_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)

        return output_path, script

    def generate_audio_from_text(
        self,
        text: str,
        output_dir: str = "generated_audio",
        filename: Optional[str] = None,
        voice_id: Optional[str] = None
    ) -> str:
        """
        Generate audio from raw text.

        Args:
            text: The text to convert to speech
            output_dir: Directory to save the generated audio file
            filename: Optional custom filename (auto-generated if not provided)
            voice_id: Optional custom voice ID (uses default if not provided)

        Returns:
            Path to the generated audio file
        """
        # Use provided voice_id or fall back to default
        voice = voice_id or self.voice_id

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audio_{timestamp}.mp3"

        output_path = os.path.join(output_dir, filename)

        # Generate audio using ElevenLabs
        audio = self.client.text_to_speech.convert(
            voice_id=voice,
            text=text,
            model_id="eleven_multilingual_v2"
        )

        # Save the audio file
        with open(output_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)

        return output_path

    def _create_podcast_script(self, articles: List[Dict[str, Any]]) -> str:
        """
        Create a podcast-style script from articles.

        Args:
            articles: List of article dictionaries

        Returns:
            Formatted script text
        """
        script_parts = []

        # Introduction
        script_parts.append(
            "Welcome to your personalized news podcast. "
            f"Here are the top {len(articles)} stories for you today.\n\n"
        )

        # Process each article
        for idx, article in enumerate(articles, 1):
            # Use summary if available, otherwise use truncated text
            content = article.get('summary') or article.get('text', '')

            # Truncate very long content
            if len(content) > 1000:
                content = content[:1000] + "..."

            # Add article to script
            category = article.get('category_name', 'General')
            source = article.get('source', 'Unknown source')

            script_parts.append(
                f"Story {idx}: {category}\n"
                f"{content}\n"
                f"Source: {source}\n\n"
            )

        # Conclusion
        script_parts.append(
            "That's all for today's news. Thank you for listening!"
        )

        return "".join(script_parts)

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices from ElevenLabs.

        Returns:
            List of voice dictionaries with id and name
        """
        voices = self.client.voices.get_all()
        return [
            {
                "id": voice.voice_id,
                "name": voice.name,
                "category": voice.category if hasattr(voice, 'category') else None
            }
            for voice in voices.voices
        ]


# Global TTS service instance
tts_service = TTSService()
