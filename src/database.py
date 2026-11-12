
import psycopg2
import os
from dotenv import load_dotenv

# Load database credentials
load_dotenv()

def get_connection():
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

        print("PostgreSQL connected successfully!")

        return connection

    except Exception as error:
        print("Database connection failed:", error)
        return None


if __name__ == "__main__":
    connection = get_connection()

    if connection:
        connection.close()
        print("Database connection closed.")
