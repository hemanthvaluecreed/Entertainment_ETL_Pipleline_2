import psycopg

from config import DB_CONFIG
from logger.loggerConfig import logger


def get_connection():
    return psycopg.connect(**DB_CONFIG)


def run_validation():
    logger.info("VALIDATION STARTED")

    validation_queries = {
        "Total Shows": """
            SELECT COUNT(*)
            FROM Shows;
        """,

        "Unique Show IDs": """
            SELECT COUNT(DISTINCT show_id)
            FROM Shows;
        """,

        "Duplicate Show IDs": """
            SELECT COUNT(*)
            FROM (
                SELECT show_id
                FROM Shows
                GROUP BY show_id
                HAVING COUNT(*) > 1
            ) AS duplicates;
        """,

        "Duplicate Schedule IDs": """
            SELECT COUNT(*)
            FROM (
                SELECT schedule_id
                FROM Shows
                WHERE schedule_id IS NOT NULL
                GROUP BY schedule_id
                HAVING COUNT(*) > 1
            ) AS duplicates;
        """,

        "Orphan ShowGenres → Shows": """
            SELECT COUNT(*)
            FROM ShowGenres sg
            LEFT JOIN Shows s
                ON sg.show_id = s.show_id
            WHERE s.show_id IS NULL;
        """,

        "Orphan ShowGenres → Genres": """
            SELECT COUNT(*)
            FROM ShowGenres sg
            LEFT JOIN Genres g
                ON sg.genre_id = g.genre_id
            WHERE g.genre_id IS NULL;
        """,

        "Orphan ShowScheduleDays → Shows": """
            SELECT COUNT(*)
            FROM ShowScheduleDays ssd
            LEFT JOIN Shows s
                ON ssd.schedule_id = s.schedule_id
            WHERE s.schedule_id IS NULL;
        """,

        "Orphan ShowScheduleDays → ScheduleDays": """
            SELECT COUNT(*)
            FROM ShowScheduleDays ssd
            LEFT JOIN ScheduleDays sd
                ON ssd.day_id = sd.day_id
            WHERE sd.day_id IS NULL;
        """,

        "Missing Show Names": """
            SELECT COUNT(*)
            FROM Shows
            WHERE show_name IS NULL
               OR TRIM(show_name) = '';
        """,

        "Invalid Ratings": """
            SELECT COUNT(*)
            FROM Shows
            WHERE rating IS NOT NULL
              AND (rating < 0 OR rating > 10);
        """,

        "Invalid Runtime": """
            SELECT COUNT(*)
            FROM Shows
            WHERE runtime_minutes IS NOT NULL
              AND runtime_minutes <= 0;
        """,

        "Invalid Average Runtime": """
            SELECT COUNT(*)
            FROM Shows
            WHERE average_runtime_minutes IS NOT NULL
              AND average_runtime_minutes <= 0;
        """,

        "Invalid Genre Count": """
            SELECT COUNT(*)
            FROM Shows
            WHERE genre_count IS NOT NULL
              AND genre_count < 0;
        """,
    }

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:

                validation_results = {}

                for name, query in validation_queries.items():
                    cursor.execute(query)
                    result = cursor.fetchone()[0]

                    validation_results[name] = result

                    logger.info(
                        "Validation | %s: %s",
                        name,
                        result
                    )

                logger.info("VALIDATION COMPLETED")

                return validation_results

    except Exception:
        logger.exception("VALIDATION FAILED")
        raise