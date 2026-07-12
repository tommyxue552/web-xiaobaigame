
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
db_path = r"C:\Users\xueta\Documents\web-xiaobaigame\backend\xiaobai.db"
conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:")
for t in tables:
    print(" ", t[0])
conn.close()

