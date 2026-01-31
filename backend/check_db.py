"""Check database contents"""
import sqlite3

conn = sqlite3.connect('datasheet_selector.db')
cursor = conn.cursor()

print("=== TABLES ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

print("\n=== DATASHEETS ===")
cursor.execute("SELECT id, name, status, progress_percent, error_message FROM datasheets")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  ID: {row[0][:8]}... | Name: {row[1]} | Status: {row[2]} | Progress: {row[3]}% | Error: {row[4]}")
else:
    print("  (No datasheets found)")

print("\n=== PART SCHEMAS ===")
cursor.execute("SELECT COUNT(*) FROM part_schemas")
print(f"  Count: {cursor.fetchone()[0]}")

conn.close()
