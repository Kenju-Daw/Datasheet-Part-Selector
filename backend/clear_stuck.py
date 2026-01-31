"""Clear stuck database entries"""
import sqlite3

conn = sqlite3.connect('datasheet_selector.db')
cursor = conn.cursor()

print("Deleting stuck/error records...")
cursor.execute("DELETE FROM datasheets WHERE status IN ('PARSING', 'ERROR', 'PENDING')")
deleted = cursor.rowcount
conn.commit()
print(f"Deleted {deleted} records")

conn.close()
print("Done! Database is clean for fresh uploads.")
