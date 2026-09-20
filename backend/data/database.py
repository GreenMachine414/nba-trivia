import os
from pathlib import Path

import psycopg2

from dotenv import load_dotenv


load_dotenv(Path(__file__).parent.parent.parent / ".env")


class Database:
    def __init__(self):
        self.host = os.getenv("PGHOST")
        self.port = os.getenv("PGPORT")
        self.database = os.getenv("PGDATABASE")
        self.user = os.getenv("PGUSER")
        self.password = os.getenv("PGPASSWORD")
        self.connection = None

    def connect(self):
        self.connection = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.database,
            user=self.user,
            password=self.password,
        )

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


db = Database()