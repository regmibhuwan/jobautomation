# Job Automation Platform

Tech job scraping, resume parsing, and automated application workflow built with FastAPI, Streamlit, and Playwright.

## Local Development

1. Create a virtual environment (`python -m venv .venv`) and activate it.
2. Install dependencies: `pip install -r requirements.txt`.
3. Initialize the SQLite database:
   ```bash
   python db/init_db.py
   ```
4. Populate jobs by running scrapers in `scrapers/` (optional).
5. Start the API:
   ```bash
   uvicorn api:app --host 0.0.0.0 --port 8000
   ```
6. In a new terminal, launch the Streamlit frontend:
   ```bash
   streamlit run frontend.py
   ```

## Render Deployment

### Repository Setup

1. Commit this project to a new GitHub repository. The Render dashboard will deploy directly from Git.
2. Ensure the repo contains at minimum:
   - `api.py`
   - `frontend.py`
   - `automation/`
   - `scrapers/`
   - `db/`
   - `requirements.txt`
   - `render.yaml`

### Deploy the API Service

1. Sign into [Render](https://dashboard.render.com) and click **New > Web Service**.
2. Choose your GitHub repository and select the branch to deploy.
3. Render will detect `render.yaml` and prompt to create the `jobautomation-api` service.
4. Confirm the configuration:
   - Build command: `pip install -r requirements.txt && playwright install --with-deps chromium`
   - Start command: `uvicorn api:app --host 0.0.0.0 --port 8000`
   - Disk: Render will create `jobs-db` mounted at `/var/data`.
5. Trigger the first deploy and wait for the service to become live.

### Deploy the Frontend Service

When you deploy via `render.yaml`, Render creates the second service automatically:

- Service name: `jobautomation-frontend`
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run frontend.py --server.address=0.0.0.0 --server.port=$PORT`
- The environment variable `API_BASE_URL` is automatically set to the API service URL by the `fromService` link in `render.yaml`.

After the build completes, visit the URL Render assigns to the frontend to interact with the dashboard.

### Playwright Headless Mode

Render deploys Playwright in headless mode by default using the `PLAYWRIGHT_HEADLESS` environment variable. When running locally you can disable headless browsing by setting `PLAYWRIGHT_HEADLESS=false` before executing automation.

### Database Persistence

The API service uses a Render persistent disk mapped to `/var/data/jobs.db`. The disk retains scraped jobs and application records across deploys. If you need seed data on first deploy, run any scrapers manually once the API is live.

## Render CLI Commands

If you prefer deploying from the terminal, install the Render CLI (`npm install -g render-cli`) and run:

```bash
render login
render blueprint deploy render.yaml
```

Follow the prompts to select the account and region. Render provisions both services per the blueprint file.

## Monitoring

- FastAPI service logs are visible under the **Logs** tab of the `jobautomation-api` service.
- Streamlit logs are available under the frontend service logs.
- Use Render cron jobs or background workers if you plan to schedule scrapers.


