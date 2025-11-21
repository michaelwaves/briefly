"""
Test script for the news with audio generation endpoint

This will:
1. Search for AI/ML/Startup news with specific keywords
2. Extract full article content
3. Generate 2-minute summaries using Azure OpenAI
4. Create audio files using ElevenLabs
5. Store everything in the database
"""
import requests
import json
from datetime import datetime

# API endpoint
API_URL = "http://localhost:8001"  # parallel_api runs on 8001
ENDPOINT = f"{API_URL}/news/generate-with-audio"

def test_news_with_audio():
    """Test the complete news with audio workflow"""

    print("\n" + "="*80)
    print("TESTING: News with Audio Generation")
    print("="*80 + "\n")

    # Request payload
    payload = {
        "query": "Latest news on AI, Machine Learning, and Startups",
        "max_articles": 10,
        "category_id": None,
        "relevance_score": 9,
        "target_duration_minutes": 2,
        "voice_id": None  # Will use default voice
    }

    print("Request:")
    print(json.dumps(payload, indent=2))
    print("\n" + "-"*80 + "\n")

    # Make request
    print(f"Calling: POST {ENDPOINT}")
    print("This will take a few minutes (searching, extracting, summarizing, generating audio)...\n")

    try:
        response = requests.post(ENDPOINT, json=payload, timeout=600)  # 10 min timeout

        if response.status_code == 200:
            result = response.json()

            print("\n" + "="*80)
            print("SUCCESS!")
            print("="*80 + "\n")

            print(f"Query: {result['query']}")
            print(f"Articles Found: {result['articles_found']}")
            print(f"Articles Processed: {result['articles_processed']}")
            print(f"Articles with Audio: {result['articles_with_audio']}")

            print("\n" + "-"*80)
            print("GENERATED ARTICLES:")
            print("-"*80 + "\n")

            for idx, article in enumerate(result['articles'], 1):
                print(f"{idx}. Article ID: {article['article_id']}")
                print(f"   Title: {article['title'][:80]}...")
                print(f"   Source: {article['source']}")
                print(f"   Audio File: {article['audio_filename']}")
                print(f"   Audio Path: {article['audio_path']}")
                print(f"   Summary Length: {article['summary_word_count']} words")
                print()

            if result['errors']:
                print("\n" + "-"*80)
                print("ERRORS:")
                print("-"*80 + "\n")
                for error in result['errors']:
                    print(f"  - {error}")

            print("\n" + "="*80)
            print(f"TOTAL: Generated {result['articles_with_audio']} audio files")
            print("="*80 + "\n")

        else:
            print(f"\n✗ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("\n✗ Request timed out (took longer than 10 minutes)")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")


if __name__ == "__main__":
    test_news_with_audio()
