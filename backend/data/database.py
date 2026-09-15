import os
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


class Database:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.connection = None

    def connect(self):
        self.connection = psycopg2.connect(self.database_url)

    def ensure_connected(self):
        if self.connection is None or self.connection.closed:
            self.connect()
            return

        try:
            self.connection.rollback()
        except Exception:
            self.connect()

    def close(self):
        if self.connection:
            self.connection.close()

    def load_data(self, table, data):
        cursor = self.connection.cursor()
        try:
            if not data:
                return
            columns = list(data[0].model_dump().keys())
            column_names = ", ".join(columns)

            values = [tuple(item.model_dump().values()) for item in data]

            sql = f"INSERT INTO {table} ({column_names}) VALUES %s"
            execute_values(cursor, sql, values)

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()


db = Database()