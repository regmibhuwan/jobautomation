import sqlite3
from typing import Optional


def create_tables(db_path: Optional[str] = None):
    path = db_path or "jobs.db"
    conn = sqlite3.connect(path)
    c = conn.cursor()

    c.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    location TEXT,
    company TEXT,
    url TEXT UNIQUE,   -- make URL unique
    status TEXT,
    date_posted TEXT,
    last_checked TEXT
)
""")

    c.execute("""
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    applied_date TEXT,
    status TEXT DEFAULT 'applied',
    notes TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs (id)
)
""")


    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Database initialized: jobs.db")
