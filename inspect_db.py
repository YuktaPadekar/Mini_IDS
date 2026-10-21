import argparse
from pathlib import Path
import sqlite3
import sys

from storage.database import DEFAULT_DB_PATH, DatabaseManager


def inspect_database(db_path: Path) -> None:
    print(f"Inspecting SQLite database: {db_path}")
    if not db_path.exists():
        print(f"Note: Database file does not exist yet. Initializing schema...")
        db = DatabaseManager(db_path)
        db.init_db()
        db.close()

    connection = sqlite3.connect(str(db_path))
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()

    if not tables:
        print("No user tables found. Initializing schema via DatabaseManager...")
        db = DatabaseManager(db_path)
        db.init_db()
        db.close()
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()

    print(f"\nTables in database ({len(tables)} found):")
    for (table_name,) in tables:
        count = connection.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]
        print(f"\n--- Table: {table_name} ({count:,} rows) ---")

        columns = connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        for column in columns:
            cid, name, col_type, notnull, dflt_value, pk = column
            pk_marker = " [PK]" if pk else ""
            print(f"  {name:<24} {col_type:<10} (notnull={notnull}){pk_marker}")

    connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect Mini-IDS SQLite database schema and row counts.")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH}).",
    )
    args = parser.parse_args()
    inspect_database(args.db)
