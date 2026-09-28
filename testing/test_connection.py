import psycopg

from config import DB_CONFIG


try:
    with psycopg.connect(**DB_CONFIG) as conn:
        print("Connected to PostgreSQL successfully!")

        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()

            print("PostgreSQL version:")
            print(version[0])

except Exception as e:
    print("Database connection failed.")
    print(f"Error: {e}")