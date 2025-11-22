from typing import Optional
from database import db


class PodcastService:
    @staticmethod
    def create_podcast_record(
        user_id: int,
        script: str,
        s3_link: str,
        spotify_link: Optional[str] = None
    ) -> int:
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO podcasts (user_id, script, s3_link, spotify_link)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (user_id, script, s3_link, spotify_link)
            )
            result = cursor.fetchone()
            return result['id']

    @staticmethod
    def get_podcast_by_id(podcast_id: int):
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, script, spotify_link, s3_link, date_created, user_id
                FROM podcasts
                WHERE id = %s
                """,
                (podcast_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def get_user_podcasts(user_id: int, limit: int = 10):
        with db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, script, spotify_link, s3_link, date_created, user_id
                FROM podcasts
                WHERE user_id = %s
                ORDER BY date_created DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            return cursor.fetchall()


podcast_service = PodcastService()
