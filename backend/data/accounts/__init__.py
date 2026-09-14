from pathlib import Path

from data.database import db

SCHEMA_PATH = Path(__file__).parent / "auth_schema.sql"


def main():
    db.connect()

    with open(SCHEMA_PATH) as f:
        schema = f.read()

    cursor = db.connection.cursor()
    cursor.execute(schema)
    db.connection.commit()
    cursor.close()

    db.close()
    print("Auth schema created (or already existed).")


if __name__ == "__main__":
    main()