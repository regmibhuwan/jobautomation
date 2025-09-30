import sqlite3

conn = sqlite3.connect("jobs.db")
c = conn.cursor()

c.execute("SELECT id, title, location, company, url FROM jobs LIMIT 5")
rows = c.fetchall()

for row in rows:
    print(row)

conn.close()
