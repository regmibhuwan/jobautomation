import sqlite3
import os
from playwright.sync_api import sync_playwright
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs.db")

def is_tech_job(title):
    """Check if job title contains tech-related keywords"""
    tech_keywords = [
        'software', 'engineer', 'developer', 'programmer', 'architect', 'data scientist',
        'machine learning', 'ai', 'backend', 'frontend', 'full stack', 'devops',
        'cloud', 'aws', 'azure', 'python', 'java', 'javascript', 'react', 'node',
        'mobile', 'ios', 'android', 'web', 'api', 'database', 'sql', 'analytics',
        'security', 'cyber', 'infrastructure', 'platform', 'system', 'tech lead',
        'senior', 'staff', 'principal', 'director', 'manager', 'head of engineering'
    ]
    
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in tech_keywords)

def save_job(title, location, url):
    # Only save tech jobs
    if not is_tech_job(title):
        return
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT INTO jobs (title, location, company, url, status, date_posted, last_checked)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(url) DO UPDATE SET
        title=excluded.title,
        location=excluded.location,
        company=excluded.company,
        status='active',
        last_checked=excluded.last_checked
    """, (
        title, location, "AutoDesk", url, "active",
        datetime.now().strftime("%Y-%m-%d"),
        datetime.now().strftime("%Y-%m-%d")
    ))
    conn.commit()
    conn.close()

def scrape_autodesk_jobs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://www.autodesk.com/careers/search-jobs")
        page.wait_for_timeout(5000)

        # Try multiple selectors for AutoDesk jobs
        jobs = page.query_selector_all("a[href*='/careers/']")
        if not jobs:
            jobs = page.query_selector_all("a.job-title-link")
        if not jobs:
            jobs = page.query_selector_all("a[data-testid*='job']")
        if not jobs:
            jobs = page.query_selector_all("a[href*='job']")
            
        print("Found", len(jobs), "jobs")  # Debug: how many jobs found

        for job in jobs:
            title = job.inner_text().strip()
            url = job.get_attribute("href")
            print("DEBUG:", title, url)  # Debug: show each job

            if url and url.startswith("/"):
                url = "https://www.autodesk.com" + url

            location = "N/A"

            if title and url:
                save_job(title, location, url)

        browser.close()

if __name__ == "__main__":
    scrape_autodesk_jobs()
    print("✅ AutoDesk jobs scraping complete.")