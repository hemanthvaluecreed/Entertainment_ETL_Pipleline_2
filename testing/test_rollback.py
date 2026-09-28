import psycopg

from config import DB_CONFIG
from logger.loggerConfig import logger


TEST_SHOW_ID = 999999999


def test_rollback():

    connection = psycopg.connect(**DB_CONFIG)

    try:

        with connection.cursor() as cursor:

            logger.info("ROLLBACK TEST STARTED")

            # Step 1: Insert temporary record
            cursor.execute(
                """
                INSERT INTO Shows (
                    show_id,
                    show_name
                )
                VALUES (%s, %s);
                """,
                (TEST_SHOW_ID, "ROLLBACK TEST SHOW")
            )

            logger.info("Temporary test record inserted")

            # Step 2: Deliberately create failure
            cursor.execute(
                """
                INSERT INTO Shows (
                    show_id,
                    show_name
                )
                VALUES (%s, %s);
                """,
                (TEST_SHOW_ID, "DUPLICATE TEST SHOW")
            )

            connection.commit()

    except Exception:

        logger.exception(
            "Expected failure occurred. Rolling back transaction."
        )

        connection.rollback()

    finally:

        connection.close()

    # Verify rollback
    connection = psycopg.connect(**DB_CONFIG)

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM Shows
                WHERE show_id = %s;
                """,
                (TEST_SHOW_ID,)
            )

            count = cursor.fetchone()[0]

            if count == 0:
                logger.info(
                    "ROLLBACK TEST PASSED: temporary record does not exist."
                )
                print("ROLLBACK TEST PASSED")
            else:
                logger.error(
                    "ROLLBACK TEST FAILED: temporary record still exists."
                )
                print("ROLLBACK TEST FAILED")

    finally:
        connection.close()


if __name__ == "__main__":
    test_rollback()