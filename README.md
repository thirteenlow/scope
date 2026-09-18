# Sync

Sync turns simulated Jira and Git activity into evidence-backed monthly team updates.

## Requirements

- Python 3.11+
- Node.js 20.19+ or 22.12+

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
fastapi dev app/main.py --port 8000
```

API documentation: http://localhost:8000/docs

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Application: http://localhost:5173

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

## Demo workflow

1. Open the dashboard.
2. Inspect completed, active, blocked, and stale work.
3. Select a developer update.
4. Approve it.
5. Generate the monthly meeting report.

All people, projects, issues, commits, and pull requests are fictional.

