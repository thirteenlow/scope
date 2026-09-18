# Sync

Sync turns simulated Jira and Git activity into evidence-backed monthly team updates.

## Prototype features

- Simulated login for four developers and one PM
- Backend-enforced ownership: developers edit only their update; PM edits all
- Commit-derived update suggestions bounded by the monthly meeting cycle
- Editable completed, in-progress, and blocker items
- Clickable simulated Jira issues and Git commits
- In-context cycle timeline for review cutoff and monthly meeting
- Meeting notes with reviewable Jira create/carry-over actions
- Explainable rule-based insights and delivery charts

The identity switcher is a demo replacement for SSO. Application state is held
in memory and resets when FastAPI restarts; the next production step is a real
database and authentication provider.

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

1. Use the identity switcher to compare developer and PM permissions.
2. Accept a Git-derived suggestion or create a manual blocker.
3. Open its simulated Jira/Git evidence, rendered as realistic product pages.
4. Review the cycle calendar and mark updates ready.
5. Sign in as Weifa (PM), record meeting notes, and propose Jira actions.

All people, projects, issues, commits, and pull requests are fictional.
