# FinSight AI

FinSight AI is an evidence-first financial research dashboard for Indian listed
companies. It uses Google Finance as the primary market-data source, TinyFish
for authenticated search, page retrieval, and metered browser-agent runs, and
TinyFish Agent API for structured synthesis. The application returns concise financial insights,
source links, risks, developments, and chart-ready metrics.

## Architecture

```text
Company form
    |
    v
FastAPI API (/api/research)
    |
    +--> News Agent ------> TinyFish Search + Fetch
    |
    +--> History Agent ---> TinyFish Search + Fetch
    |
    +--> Analyst Agent ---> TinyFish structured analysis
    |
    v
ResearchReport JSON
    |
    v
Lightweight browser dashboard
```

The two TinyFish research agents run concurrently. Source failures are retained
as compact notes rather than preventing the rest of the report from completing.
Financial series are returned only when numeric values are explicitly present in
the collected evidence; the application does not invent or interpolate values.

## Features

- Recent company news and corporate disclosures.
- Google Finance quote, market-data, and financial-history context.
- Historical events and evidence classifications.
- BUY, HOLD, SELL, or WATCH signal.
- Concise assessment, positives, risks, and watch items.
- Maximum five visible findings per major section.
- Financial metric cards.
- Line charts for multi-period financial series.
- Bar charts for shorter financial series.
- Source links for every finding.
- SQLite persistence for completed reports.
- CORS support for a separately hosted Lovable or React frontend.
- TinyFish attribution in the dashboard.

## Requirements

- Python 3.11 or newer.
- TinyFish API key for live web research.
- TinyFish API key for live search, browser-agent research, and analysis.
- Windows PowerShell, macOS/Linux shell, or an equivalent terminal.

## Install and run locally

From the project directory:

```powershell
python -m venv .venv
```

Activate the virtual environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set your own credentials:

```env
TINYFISH_API_KEY=your-tinyfish-api-key
DATABASE_URL=sqlite:///finsight.db
REQUEST_TIMEOUT_SECONDS=15
MOCK_MODE=false
FRONTEND_ORIGINS=http://localhost:3000,http://localhost:5173
```

Never commit `.env` or expose these credentials in a browser frontend.

Start the API and dashboard:

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

### One-command Windows launcher

After cloning the project, run this from PowerShell:

```powershell
.\start-finsight.ps1
```

The launcher:

1. Creates `.venv` if it does not exist.
2. Installs the dependencies from `requirements.txt`.
3. Creates `.env` from `.env.example` if needed.
4. Verifies that the application imports correctly.
5. Starts the FastAPI backend and built-in browser frontend.
6. Opens `http://127.0.0.1:8000`.

The backend and frontend are served by the same FastAPI process; there is no
separate frontend server to start for the included dashboard.

If PowerShell blocks local scripts, enable scripts for your user account once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then run:

```powershell
.\start-finsight.ps1
```

Keep the launcher window open while using the dashboard. Press `Ctrl+C` in that
window to stop the server.

For development auto-reload:

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## Verify the installation

Check the health endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "live_research_configured": true
}
```

Run the automated tests:

```powershell
python -m pytest -q
```

Compile-check the application:

```powershell
python -m py_compile app.py core\schemas.py agents\analyst_agent.py
```

Test the research API:

```powershell
$body = @{
  name = "Infosys Limited"
  symbol = "INFY"
  exchange = "NSE"
  days = 30
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/api/research `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Live research can take several seconds because it searches and fetches external
source pages. Some publishers block automated fetches; those URLs appear as
source notes and do not necessarily mean the entire report failed.

## Mock mode

To run without external API calls:

```env
MOCK_MODE=true
```

Mock mode is intended for UI development and automated tests. It clearly marks
the report as mock output and does not fabricate financial statistics.

## API reference

### `GET /health`

Returns application status and whether both live credentials are configured.

### `GET /`

Returns the built-in dashboard.

### `POST /api/research`

Request:

```json
{
  "name": "Infosys Limited",
  "symbol": "INFY",
  "exchange": "NSE",
  "days": 30
}
```

The response contains:

- `company`: normalized company input.
- `news.findings`: recent source-linked findings.
- `history.findings`: historical source-linked events.
- `analysis.signal`: BUY, HOLD, SELL, or WATCH.
- `analysis.financial_metrics`: latest financial metric cards.
- `analysis.financial_series`: chart-ready periods and numeric values.
- `errors`: compact source or processing notes.
- `incomplete`: whether any part of the report had an error.

Google Finance is always attempted first for the requested exchange and symbol.
Each News and History agent also runs TinyFish's metered Agent API against the
Google Finance page using `POST https://agent.tinyfish.ai/v1/automation/run`.
TinyFish then retrieves a small set of targeted official or financial sources.

## Connecting Lovable or another frontend

Deploy this FastAPI service to a public HTTPS URL, for example:

```text
https://your-finsight-api.example.com
```

Set the backend environment variable to the exact frontend origin:

```env
FRONTEND_ORIGINS=https://your-project.lovable.app
```

The frontend should call:

```text
POST https://your-finsight-api.example.com/api/research
```

Do not put `TINYFISH_API_KEY` or `GEMINI_API_KEY` in Lovable, Replit, React, or
any other browser bundle. Only expose the backend URL.

## Project structure

```text
app.py                  FastAPI application and lightweight dashboard
agents/
  news_agent.py         TinyFish recent-news agent
  history_agent.py      TinyFish historical-context agent
  analyst_agent.py      TinyFish structured synthesis
core/
  config.py             Environment configuration
  orchestrator.py       Concurrent agent execution
  prompts.py            Evidence and output constraints
  schemas.py            Pydantic response contracts
tinyfish/
  client.py             TinyFish HTTP client
  search.py             Search normalization
  fetch.py              Batched source fetching
database/
  db.py                 SQLite report persistence
tests/                  Automated test suite
```

## Security notes

- Keep all API credentials in `.env`.
- `.env` is ignored by Git.
- Rotate credentials immediately if they are exposed.
- Restrict `FRONTEND_ORIGINS` to known frontend origins.
- Do not treat the signal as personalized investment advice.
- Always verify important information using the original source links.

## Limitations

- This project is not a trading or brokerage system.
- It does not provide guaranteed predictions.
- It does not provide personalized financial advice.
- Numeric charts require explicitly reported numeric data.
- External sites may block TinyFish fetch requests.
- API response formats can change as external providers evolve.
