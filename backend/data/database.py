import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


class Database:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = os.getenv("DB_PORT")
        self.connection = None

    def connect(self):
        self.connection = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password,
            port=self.port
        )

    def ensure_connected(self):
        if self.connection is None or self.connection.closed:
            self.connect()
            return

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            self.connect()

    def close(self):
        if self.connection:
            self.connection.close()

    def load_data(self, table, data):
        cursor = self.connection.cursor()

        try:
            columns = list(data[0].model_dump().keys())

            column_names = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))

            sql = f"""
                INSERT INTO {table} ({column_names})
                VALUES ({placeholders})
            """

            for item in data:
                values = list(item.model_dump().values())
                cursor.execute(sql, values)

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()


db = Database()