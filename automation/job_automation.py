import os
import json
from playwright.async_api import async_playwright
from datetime import datetime
import sqlite3
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class JobAutomation:
    def __init__(self, resume_data=None, db_path: str | None = None):
        self.resume_data = resume_data or {}
        default_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs.db")
        self.db_path = db_path or os.getenv("DB_PATH", default_db_path)
        
    def save_application_result(self, job_id, status, notes=""):
        """Save application result to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Update application status
        c.execute("""
            UPDATE applications 
            SET status = ?, notes = ?
            WHERE job_id = ?
        """, (status, notes, job_id))
        
        conn.commit()
        conn.close()
    
    async def apply_to_uber_job(self, job_url, job_id):
        """Automate application to Uber job"""
        try:
            async with async_playwright() as p:
                headless_setting = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower()
                headless = headless_setting not in ("false", "0", "no")
                browser = await p.chromium.launch(headless=headless)
                page = await browser.new_page()
                
                try:
                    # Navigate to job page
                    await page.goto(job_url)
                    await page.wait_for_timeout(3000)
                    
                    # Look for apply button
                    apply_button = await page.query_selector("button:has-text('Apply')")
                    if not apply_button:
                        apply_button = await page.query_selector("a:has-text('Apply')")
                    
                    if apply_button:
                        await apply_button.click()
                        await page.wait_for_timeout(2000)
                        
                        # Fill out application form
                        await self._fill_uber_form(page)
                        
                        # Submit application
                        submit_button = await page.query_selector("button:has-text('Submit')")
                        if submit_button:
                            await submit_button.click()
                            await page.wait_for_timeout(3000)
                            
                            # Check for success
                            content = await page.content()
                            if "thank you" in content.lower() or "submitted" in content.lower():
                                self.save_application_result(job_id, "applied", "Successfully applied via automation")
                                return True
                            else:
                                self.save_application_result(job_id, "failed", "Application submitted but confirmation unclear")
                                return False
                        else:
                            self.save_application_result(job_id, "failed", "Submit button not found")
                            return False
                    else:
                        self.save_application_result(job_id, "failed", "Apply button not found")
                        return False
                        
                except Exception as e:
                    self.save_application_result(job_id, "failed", f"Error: {str(e)}")
                    return False
                finally:
                    await browser.close()
        except Exception as e:
            print(f"Playwright error: {str(e)}")
            self.save_application_result(job_id, "failed", f"Playwright error: {str(e)}")
            return False
    
    async def _fill_uber_form(self, page):
        """Fill out Uber application form"""
        try:
            # Fill personal information
            if self.resume_data.get('contact', {}).get('email'):
                email_field = await page.query_selector("input[type='email']")
                if email_field:
                    await email_field.fill(self.resume_data['contact']['email'])
            
            # Fill name fields
            if self.resume_data.get('contact', {}).get('name'):
                name_parts = self.resume_data['contact']['name'].split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                first_name_field = await page.query_selector("input[name*='first']")
                if first_name_field:
                    await first_name_field.fill(first_name)
                
                last_name_field = await page.query_selector("input[name*='last']")
                if last_name_field:
                    await last_name_field.fill(last_name)
            
            # Fill phone
            if self.resume_data.get('contact', {}).get('phone'):
                phone_field = await page.query_selector("input[type='tel']")
                if phone_field:
                    await phone_field.fill(self.resume_data['contact']['phone'])
            
            # Fill experience
            if self.resume_data.get('experience_years'):
                experience_field = await page.query_selector("input[name*='experience']")
                if experience_field:
                    await experience_field.fill(self.resume_data['experience_years'])
            
            # Upload resume if available
            resume_path = self.resume_data.get('resume_path')
            if resume_path and os.path.exists(resume_path):
                file_input = await page.query_selector("input[type='file']")
                if file_input:
                    await file_input.set_input_files(resume_path)
            
            await page.wait_for_timeout(1000)
            
        except Exception as e:
            print(f"Error filling form: {e}")
    
    async def apply_to_job(self, job_url, job_id, company):
        """Apply to job based on company"""
        if company.lower() == "uber":
            return await self.apply_to_uber_job(job_url, job_id)
        else:
            # For other companies, we'll implement later
            self.save_application_result(job_id, "pending", f"Automation not yet implemented for {company}")
            return False
    
    def get_pending_applications(self):
        """Get jobs that need to be applied to"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            SELECT j.id, j.title, j.url, j.company
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id
            WHERE j.status = 'active' AND a.id IS NULL
            ORDER BY j.date_posted DESC
        """)
        
        jobs = c.fetchall()
        conn.close()
        
        return jobs
    
    async def run_automation(self, max_applications=5):
        """Run automation for pending applications"""
        try:
            pending_jobs = self.get_pending_applications()
            
            if not pending_jobs:
                print("No pending applications found.")
                return
            
            print(f"Found {len(pending_jobs)} pending applications. Processing up to {max_applications}...")
            
            successful_applications = 0
            for job_id, title, url, company in pending_jobs[:max_applications]:
                print(f"\nApplying to: {title} at {company}")
                print(f"URL: {url}")
                
                success = await self.apply_to_job(url, job_id, company)
                if success:
                    successful_applications += 1
                    print("✅ Application successful!")
                else:
                    print("❌ Application failed!")
                
                # Wait between applications to avoid being flagged
                await asyncio.sleep(5)
            
            print(f"\nAutomation complete! {successful_applications}/{max_applications} applications successful.")
        except Exception as e:
            print(f"Automation error: {str(e)}")
            raise Exception(f"Automation error: {str(e)}")

if __name__ == "__main__":
    # Example usage
    resume_data = {
        'contact': {
            'email': 'your.email@example.com',
            'name': 'John Doe',
            'phone': '+1234567890'
        },
        'experience_years': '5',
        'resume_path': 'path/to/resume.pdf'
    }
    
    async def main():
        automation = JobAutomation(resume_data)
        await automation.run_automation(max_applications=3)
    
    asyncio.run(main())

