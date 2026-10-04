import os
import pandas as pd
import psycopg

from config import DB_CONFIG, BATCH_SIZE
from logger.loggerConfig import logger

PROCESSED_DIR = os.path.join("data", "processed")
# 1. DATABASE CONNECTION
def get_connection():
    """Create and return a PostgreSQL database connection."""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        logger.info("Database connection established.")
        return conn

    except Exception:
        logger.exception("Failed to connect to PostgreSQL.")
        raise

# 2. CSV READER

def read_csv(filename):
    """Read a processed CSV file into a Pandas DataFrame."""
    path = os.path.join(PROCESSED_DIR, filename)

    try:
        df = pd.read_csv(path)
        logger.info("Loaded CSV: %s | Rows: %d", filename, len(df))
        return df

    except Exception:
        logger.exception("Failed to read CSV: %s", path)
        raise
# 3. HELPER FOR NaN -> None


def clean_value(value):
    """
    Convert Pandas missing values into Python None.

    PostgreSQL expects None for SQL NULL values when using
    parameterized queries.
    """
    if pd.isna(value):
        return None

    return value

# GENERIC BATCH EXECUTOR
def execute_batch(cursor, sql, rows):
    """
    Execute parameterized INSERT/UPSERT statements in batches.
    """

    total_rows = len(rows)

    for start in range(0, total_rows, BATCH_SIZE):

        batch = rows[start:start + BATCH_SIZE]

        cursor.executemany(sql, batch)

        logger.info("Processed batch: %d - %d of %d",start + 1,min(start + BATCH_SIZE, total_rows),total_rows)

# 5. LOAD GENRES

def load_genres(cursor):
    """Load Genres using idempotent UPSERT."""

    df = read_csv("genres.csv")

    sql = """
        INSERT INTO Genres (
            genre_id,
            genre_name
        )
        VALUES (%s, %s)
        ON CONFLICT (genre_id)
        DO UPDATE SET
            genre_name = EXCLUDED.genre_name;
    """

    rows = [
        (
            clean_value(row["genre_id"]),
            clean_value(row["genre_name"])
        )
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, sql, rows)

    logger.info("Genres loaded successfully: %d rows", len(rows))

# 6. LOAD TELEVISION NETWORKS

def load_networks(cursor):
    """Load television networks using idempotent UPSERT."""

    df = read_csv("television_network.csv")

    sql = """
        INSERT INTO Television_Network (
            network_id,
            name,
            country,
            country_code,
            timezone
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (network_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            country = EXCLUDED.country,
            country_code = EXCLUDED.country_code,
            timezone = EXCLUDED.timezone;
    """

    rows = [
        (
            clean_value(row["network_id"]),
            clean_value(row["name"]),
            clean_value(row["country"]),
            clean_value(row["country_code"]),
            clean_value(row["timezone"])
        )
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, sql, rows)

    logger.info(
        "Television networks loaded successfully: %d rows",
        len(rows)
    )

# 7. LOAD WEB CHANNELS
def load_web_channels(cursor):
    """Load web channels using idempotent UPSERT."""

    df = read_csv("web_channel.csv")

    sql = """
        INSERT INTO WebChannel (
            web_channel_id,
            name,
            official_site
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (web_channel_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            official_site = EXCLUDED.official_site;
    """

    rows = [
        (
            clean_value(row["web_channel_id"]),
            clean_value(row["name"]),
            clean_value(row["official_site"])
        )
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, sql, rows)

    logger.info(
        "Web channels loaded successfully: %d rows",
        len(rows)
    )

# LOAD SCHEDULE DAYS
def load_schedule_days(cursor):
    """Load schedule days using idempotent UPSERT."""

    df = read_csv("schedule_days.csv")

    sql = """
        INSERT INTO ScheduleDays (
            day_id,
            day_name
        )
        VALUES (%s, %s)
        ON CONFLICT (day_id)
        DO UPDATE SET
            day_name = EXCLUDED.day_name;
    """

    rows = [
        (
            clean_value(row["day_id"]),
            clean_value(row["day_name"])
        )
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, sql, rows)

    logger.info(
        "Schedule days loaded successfully: %d rows",
        len(rows)
    )

# LOAD SHOWS

def load_shows(cursor):
    """
    Load Shows using an idempotent UPSERT.

    show_id is the primary key, so an existing show is updated
    instead of inserted again.
    """

    df = read_csv("shows.csv")

    sql = """
        INSERT INTO Shows (
            show_id,
            show_name,
            show_type,
            language,
            status,
            runtime_minutes,
            average_runtime_minutes,
            premiered_date,
            ended_date,
            official_site,
            schedule_id,
            schedule_time,
            rating,
            network_id,
            web_channel_id,
            summary,
            updated_at,
            genre_count,
            has_rating,
            show_duration_days,
            is_currently_running
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s
        )
        ON CONFLICT (show_id)
        DO UPDATE SET
            show_name = EXCLUDED.show_name,
            show_type = EXCLUDED.show_type,
            language = EXCLUDED.language,
            status = EXCLUDED.status,
            runtime_minutes = EXCLUDED.runtime_minutes,
            average_runtime_minutes = EXCLUDED.average_runtime_minutes,
            premiered_date = EXCLUDED.premiered_date,
            ended_date = EXCLUDED.ended_date,
            official_site = EXCLUDED.official_site,
            schedule_id = EXCLUDED.schedule_id,
            schedule_time = EXCLUDED.schedule_time,
            rating = EXCLUDED.rating,
            network_id = EXCLUDED.network_id,
            web_channel_id = EXCLUDED.web_channel_id,
            summary = EXCLUDED.summary,
            updated_at = EXCLUDED.updated_at,
            genre_count = EXCLUDED.genre_count,
            has_rating = EXCLUDED.has_rating,
            show_duration_days = EXCLUDED.show_duration_days,
            is_currently_running = EXCLUDED.is_currently_running;
    """

    rows = [
        (
            clean_value(row["show_id"]),
            clean_value(row["show_name"]),
            clean_value(row["show_type"]),
            clean_value(row["language"]),
            clean_value(row["status"]),
            clean_value(row["runtime_minutes"]),
            clean_value(row["average_runtime_minutes"]),
            clean_value(row["premiered_date"]),
            clean_value(row["ended_date"]),
            clean_value(row["official_site"]),
            clean_value(row["schedule_id"]),
            clean_value(row["schedule_time"]),
            clean_value(row["rating"]),
            clean_value(row["network_id"]),
            clean_value(row["web_channel_id"]),
            clean_value(row["summary"]),
            clean_value(row["updated_at"]),
            clean_value(row["genre_count"]),
            clean_value(row["has_rating"]),
            clean_value(row["show_duration_days"]),
            clean_value(row["is_currently_running"])
        )
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, sql, rows)

    logger.info("Shows loaded successfully: %d rows", len(rows))


# LOAD SHOW-GENRE RELATIONSHIP

def load_show_genres(cursor):
    """Load ShowGenres many-to-many relationship."""

    df = read_csv("show_genres.csv")

    sql = """
        INSERT INTO ShowGenres (
            show_id,
            genre_id
        )
        VALUES (%s, %s)
        ON CONFLICT (show_id, genre_id)
        DO NOTHING;
    """

    rows = [
        (
            clean_value(row["show_id"]),
            clean_value(row["genre_id"])
        )
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, sql, rows)

    logger.info(
        "ShowGenres loaded successfully: %d rows",
        len(rows)
    )


# ============================================================
# 11. LOAD SHOW-SCHEDULE-DAY RELATIONSHIP
# ============================================================

def load_show_schedule_days(cursor):
    """Load ShowScheduleDays relationship."""

    df = read_csv("show_schedule_days.csv")

    sql = """
        INSERT INTO ShowScheduleDays (
            schedule_id,
            day_id
        )
        VALUES (%s, %s)
        ON CONFLICT (schedule_id, day_id)
        DO NOTHING;
    """

    rows = [
        (
            clean_value(row["schedule_id"]),
            clean_value(row["day_id"])
        )
        for _, row in df.iterrows()
    ]

    execute_batch(cursor, sql, rows)

    logger.info(
        "ShowScheduleDays loaded successfully: %d rows",
        len(rows)
    )


# ============================================================
# 12. COMPLETE PIPELINE LOAD
# ============================================================

def load_all():
    """
    Load all processed datasets inside one database transaction.

    If every dataset loads successfully:
        COMMIT

    If any dataset fails:
        ROLLBACK
    """

    conn = None

    try:
        conn = get_connection()

        with conn.cursor() as cursor:

            logger.info("Starting database load.")

            # Parent / lookup tables
            load_genres(cursor)
            load_networks(cursor)
            load_web_channels(cursor)
            load_schedule_days(cursor)

            # Main table
            load_shows(cursor)

            # Relationship tables
            load_show_genres(cursor)
            load_show_schedule_days(cursor)

        # All operations succeeded
        conn.commit()

        logger.info("Database transaction committed successfully.")
        logger.info("All datasets loaded successfully.")

    except Exception:
        if conn is not None:
            conn.rollback()

        logger.exception(
            "Database load failed. Transaction rolled back."
        )

        raise

    finally:
        if conn is not None:
            conn.close()
            logger.info("Database connection closed.")

