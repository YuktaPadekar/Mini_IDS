import argparse
from pathlib import Path
import sqlite3
import sys

from storage.database import DEFAULT_DB_PATH, DatabaseManager


def inspect_alerts(db_path: Path) -> None:
    print(f"Inspecting alerts in SQLite database: {db_path}")
    if not db_path.exists():
        print(f"Note: Database file does not exist yet at {db_path}. Initializing empty schema...")
        db = DatabaseManager(db_path)
        db.init_db()
        db.close()

    connection = sqlite3.connect(str(db_path))

    # Verify alerts table exists
    has_alerts = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='alerts'"
    ).fetchone()
    if not has_alerts:
        print("Table 'alerts' not found. Initializing schema via DatabaseManager...")
        db = DatabaseManager(db_path)
        db.init_db()
        db.close()

    total_alerts = connection.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    total_packets = connection.execute("SELECT COUNT(*) FROM packets").fetchone()[0]

    print(f"\nPacket table total: {total_packets:,} packets")
    print(f"Total alert rows:   {total_alerts:,} alerts")

    if total_alerts == 0:
        print("\n[INFO] No alerts recorded in this database yet.")
        print("To populate alerts, either:")
        print("  1. Ingest an offline capture: python main.py -p <capture.pcap> --hybrid")
        print("  2. Or inspect the pre-populated demo database: python inspect_alerts.py --db data/demo_synthetic.db")
        connection.close()
        return

    print("\nCounts by rule, severity, source, and destination:")
    rows = connection.execute("""
        SELECT rule_name, severity, src_ip, dst_ip, COUNT(*)
        FROM alerts
        GROUP BY rule_name, severity, src_ip, dst_ip
        ORDER BY rule_name, severity, src_ip, dst_ip
    """).fetchall()

    for row in rows:
        print(f"  {row[0]:<25} | {row[1]:<8} | {row[2]} -> {row[3]} | Count: {row[4]:,}")

    print("\nAlert timestamp range:")
    min_ts, max_ts = connection.execute("""
        SELECT MIN(timestamp), MAX(timestamp)
        FROM alerts
    """).fetchone()
    print(f"  Min: {min_ts}")
    print(f"  Max: {max_ts}")

    connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect Mini-IDS alert records and breakdown statistics.")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH}).",
    )
    args = parser.parse_args()
    inspect_alerts(args.db)