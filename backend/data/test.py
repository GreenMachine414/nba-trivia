"""
List every table in the NBA SQLite database (nba.sqlite), along with
row counts and column names for each.

Prerequisite: download and unzip the dataset first, e.g.:
    pip install kaggle
    kaggle datasets download -d wyattowalsh/basketball
    unzip basketball.zip

Then point DB_PATH below at wherever nba.sqlite ended up.
"""

import sqlite3
import os

DB_PATH = "nba.sqlite"  # change this if the file is in a different folder


def main():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Could not find '{DB_PATH}'. Update DB_PATH to the correct location "
            "of nba.sqlite after downloading/unzipping the Kaggle dataset."
        )

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Get all table names (excluding internal sqlite metadata tables)
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """)
    tables = [row[0] for row in cur.fetchall()]

    print(f"Found {len(tables)} tables in {DB_PATH}\n")
    print("=" * 70)

    # 2. For each table, print row count and column names
    for table in tables:
        # Row count
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{table}";')
            row_count = cur.fetchone()[0]
        except sqlite3.Error as e:
            row_count = f"error: {e}"

        # Column info
        cur.execute(f'PRAGMA table_info("{table}");')
        columns = [col[1] for col in cur.fetchall()]

        print(f"\nTable: {table}")
        print(f"  Rows: {row_count}")
        print(f"  Columns ({len(columns)}): {', '.join(columns)}")

    print("\n" + "=" * 70)
    print(f"Done. {len(tables)} tables listed.")

    conn.close()


if __name__ == "__main__":
    main()