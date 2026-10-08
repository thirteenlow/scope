# Scope

Scope is a code-aware feature planning assistant. A product manager discusses a feature and target timeline with Claude; Scope supplies context from a simulated existing personal budgeting product (PocketPlan), turns the conversation into evidence-backed scope options and engineering work, and syncs approved work into a simulated Jira workspace.

The project intentionally uses local mock integrations so it can be demonstrated without access to a company repository or Jira tenant.

## Stack

- Frontend: React 19, TypeScript, Vite
- Backend: FastAPI, Pydantic, pytest
- Mock existing product: `mock-pocketplan/`
- LLM: Anthropic Messages API (Claude), called only from FastAPI
- Simulated integrations: PocketPlan repository browser and Jira issue workspace

## Run it

Open two terminals.

### Backend

```bash
cd backend
py -3.12 -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Copy .env.example to .env, then add your gateway credentials
# Windows PowerShell:
Copy-Item .env.example .env

# Edit .env so it contains:
# ANTHROPIC_AUTH_TOKEN=your_real_token_here
# ANTHROPIC_BASE_URL=https://llm-gateway.aisg.sg/
# ANTHROPIC_MODEL=claude-sonnet-4-6

python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The frontend expects the API at `http://localhost:8000`; override this with `VITE_API_URL` if needed.

## Recommended demo

1. Ask Scope: “Allow users to carry unused category money into the next month. We need it within four weeks.”
2. Answer Claude's high-value clarification questions in the same conversation.
3. Click **Generate plan** when the brief is ready.
4. Compare the generated scope options in the plan drawer.
5. Inspect the linked repository evidence if needed.
6. Approve one option and create its epic, stories, and tasks in mock Jira.

## What is simulated

- Repository indexing and file citations read the local `mock-pocketplan` directory.
- Repository access and Jira writes are simulated locally.
- Feature discussion and plan generation use Claude through the configured Anthropic-compatible gateway.
- Jira creation writes to in-memory backend state and resets when the API restarts.

## API-key safety

- Put the key only in `backend/.env`; never add it to `frontend/.env`.
- `.env` is excluded by `.gitignore` and must not be committed.
- The browser sends conversation text to FastAPI. FastAPI adds code context and calls Anthropic server-side.
- The prototype sends selected PocketPlan source files to Claude. A production version should add repository permissions, secret scanning, context redaction, audit logging, and retention controls.

## Replacing mocks with real integrations

- Replace `backend/app/repository.py` with a GitHub App adapter that clones or retrieves permitted files, metadata, and pull requests.
- Replace Jira mutation methods in `backend/app/state.py` with OAuth-backed Jira Cloud REST calls.
- Keep the approval gate: analysis may draft work, but only an explicit user action should create Jira issues.
- Add embeddings or a code graph for large repositories, then provide only retrieved, permission-filtered context to the LLM.
- Store every conclusion as `verified`, `inferred`, or `open_question`, with source paths and reviewer state.

## Tests

```bash
cd backend
pytest

cd ../frontend
npm run build
```
