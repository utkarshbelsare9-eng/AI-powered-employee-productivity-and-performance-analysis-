import sqlite3
import csv
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "database", "app.db")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "csv_export")

os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print(f"Found {len(tables)} tables: {tables}\n")

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cursor.fetchall()]

    # Skip password_hash for security
    safe_cols = [c for c in cols if c != 'password_hash']
    col_str = ', '.join(safe_cols)

    cursor.execute(f"SELECT {col_str} FROM {table}")
    rows = cursor.fetchall()

    csv_path = os.path.join(OUTPUT_DIR, f"{table}.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(safe_cols)
        writer.writerows(rows)

    print(f"  [OK] {table}.csv  ({len(rows)} rows)")

conn.close()
print(f"\nAll tables exported to '{OUTPUT_DIR}/' folder.")
