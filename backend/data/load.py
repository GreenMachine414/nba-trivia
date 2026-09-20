from pathlib import Path

from data.database import db

SCHEMA_PATH = Path(__file__).parent / "accounts" / "schema.sql"


def load_schema(schema_path: Path):
    with open(schema_path, "r") as f:
        schema = f.read()

    cursor = db.connection.cursor()
    cursor.execute(schema)
    db.connection.commit()
    cursor.close()
    print(f"Schema loaded: {schema_path.name}")


def main():
    db.ensure_connected()

    load_schema(SCHEMA_PATH)

    db.close()


if __name__ == "__main__":
    main()