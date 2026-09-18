from html import escape

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from . import state
from .analysis import build_calendar, build_dashboard, build_insights, build_updates
from .auth import current_user, require_edit
from .models import AcceptSuggestion, MeetingAction, MeetingNote, MeetingWorkspace, UpdateItem, UpdateItemCreate, UpdateItemPatch, User
from .repository import get_commits, get_pull_requests, get_users

app = FastAPI(title="Sync API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health(): return {"status": "healthy", "version": "0.2.0"}


@app.get("/api/session/users")
def session_users(): return get_users()


@app.get("/api/dashboard")
def dashboard(_: User = Depends(current_user)): return build_dashboard()


@app.get("/api/insights")
def insights(_: User = Depends(current_user)): return build_insights()


@app.get("/api/calendar")
def calendar(_: User = Depends(current_user)): return build_calendar()


@app.get("/api/updates")
def updates(user: User = Depends(current_user)): return build_updates(user.id, user.role == "pm")


@app.post("/api/updates/{developer_id}/items")
def add_item(payload: UpdateItemCreate, developer_id: str, user: User = Depends(current_user)):
    require_edit(user, developer_id)
    item = UpdateItem(id=state.new_id("item"), developer_id=developer_id, **payload.model_dump(), source="manual")
    state.update_items.append(item)
    state.approved_updates.discard(developer_id)
    return item


def _find_item(item_id: str) -> UpdateItem:
    item = next((item for item in state.update_items if item.id == item_id), None)
    if not item: raise HTTPException(status_code=404, detail="Update item not found")
    return item


@app.patch("/api/update-items/{item_id}")
def edit_item(payload: UpdateItemPatch, item_id: str, user: User = Depends(current_user)):
    item = _find_item(item_id)
    require_edit(user, item.developer_id)
    for field, value in payload.model_dump(exclude_unset=True).items(): setattr(item, field, value)
    state.approved_updates.discard(item.developer_id)
    return item


@app.delete("/api/update-items/{item_id}")
def delete_item(item_id: str, user: User = Depends(current_user)):
    item = _find_item(item_id)
    require_edit(user, item.developer_id)
    state.update_items.remove(item)
    state.approved_updates.discard(item.developer_id)
    return {"deleted": item_id}


@app.post("/api/suggestions/{suggestion_id}/accept")
def accept_suggestion(payload: AcceptSuggestion, suggestion_id: str, user: User = Depends(current_user)):
    suggestion = next((item for item in state.suggestions if item.id == suggestion_id), None)
    if not suggestion: raise HTTPException(status_code=404, detail="Suggestion not found")
    require_edit(user, suggestion.developer_id)
    values = payload.model_dump(exclude_none=True)
    item = UpdateItem(
        id=state.new_id("item"), developer_id=suggestion.developer_id,
        title=values.get("title", suggestion.title), detail=values.get("detail", suggestion.detail),
        category=values.get("category", suggestion.category), evidence=suggestion.evidence, source="suggested",
    )
    state.update_items.append(item)
    state.dismissed_suggestions.add(suggestion_id)
    state.approved_updates.discard(suggestion.developer_id)
    return item


@app.delete("/api/suggestions/{suggestion_id}")
def dismiss_suggestion(suggestion_id: str, user: User = Depends(current_user)):
    suggestion = next((item for item in state.suggestions if item.id == suggestion_id), None)
    if not suggestion: raise HTTPException(status_code=404, detail="Suggestion not found")
    require_edit(user, suggestion.developer_id)
    state.dismissed_suggestions.add(suggestion_id)
    return {"dismissed": suggestion_id}


@app.post("/api/updates/{developer_id}/approve")
def approve_update(developer_id: str, user: User = Depends(current_user)):
    require_edit(user, developer_id)
    state.approved_updates.add(developer_id)
    return {"developer_id": developer_id, "approved": True}


@app.get("/api/meeting")
def meeting(_: User = Depends(current_user)):
    developer_count = sum(user.role == "developer" for user in get_users())
    return MeetingWorkspace(month="August 2026", meeting_date=state.MEETING_DATE.isoformat(), notes=state.meeting_notes, actions=state.meeting_actions, approved_updates=len(state.approved_updates), total_updates=developer_count)


@app.put("/api/meeting/notes")
def save_notes(payload: MeetingNote, user: User = Depends(current_user)):
    if user.role != "pm": raise HTTPException(status_code=403, detail="Only the PM can edit meeting notes")
    state.meeting_notes = payload.text
    return {"saved": True, "text": state.meeting_notes}


@app.post("/api/meeting/actions/suggest")
def suggest_actions(_: User = Depends(current_user)):
    actions = [MeetingAction(id=state.new_id("action"), action="carry_over", title=f"Carry {issue.key} into September", issue_key=issue.key, owner=issue.assignee) for issue in state.dynamic_issues if issue.status in {"In Progress", "Blocked"}]
    if state.meeting_notes.strip():
        actions.append(MeetingAction(id=state.new_id("action"), action="create_issue", title=f"Follow up: {state.meeting_notes.strip().splitlines()[0][:100]}"))
    state.meeting_actions = actions
    return actions


@app.post("/api/meeting/actions/{action_id}/approve")
def approve_action(action_id: str, user: User = Depends(current_user)):
    if user.role != "pm": raise HTTPException(status_code=403, detail="Only the PM can approve Jira actions")
    action = next((item for item in state.meeting_actions if item.id == action_id), None)
    if not action: raise HTTPException(status_code=404, detail="Meeting action not found")
    action.approved = True
    return action


@app.get("/mock/jira/browse/{issue_key}", response_class=HTMLResponse)
def mock_jira(issue_key: str):
    issue = next((item for item in state.dynamic_issues if item.key == issue_key), None)
    if not issue: raise HTTPException(status_code=404, detail="Issue not found")
    users = {user.id: user for user in get_users()}
    assignee = users.get(issue.assignee)
    status_class = "blocked" if issue.status == "Blocked" else "done" if issue.status == "Done" else "progress"
    return HTMLResponse(f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>{escape(issue.key)} · Jira</title><style>
    *{{box-sizing:border-box}}body{{margin:0;color:#172b4d;background:#fff;font:14px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}.top{{height:56px;display:flex;align-items:center;gap:24px;padding:0 22px;color:#fff;background:#0747a6}}.logo{{font-size:20px;font-weight:700}}.top nav{{display:flex;gap:20px;font-weight:600}}.search{{margin-left:auto;padding:8px 14px;border-radius:4px;background:#ffffff24}}.sim{{padding:5px 8px;color:#172b4d;border-radius:3px;background:#fffae6;font-size:10px;font-weight:700}}.layout{{display:grid;grid-template-columns:220px 1fr;min-height:calc(100vh - 56px)}}aside{{padding:24px 14px;background:#f4f5f7;border-right:1px solid #dfe1e6}}aside strong{{display:block;padding:9px}}aside a{{display:block;padding:9px;color:#42526e;text-decoration:none;border-radius:3px}}aside a.active{{color:#0052cc;background:#deebff}}main{{padding:34px 46px}}.crumbs{{color:#6b778c;font-size:12px}}.head{{display:flex;justify-content:space-between;align-items:start}}h1{{margin:13px 0 20px;font-size:28px;font-weight:500}}button{{padding:9px 14px;border:1px solid #dfe1e6;border-radius:3px;background:#f4f5f7;color:#172b4d;font-weight:600}}.content{{display:grid;grid-template-columns:1fr 320px;gap:54px}}h2{{font-size:16px}}.description{{min-height:150px;padding:18px;border:1px solid #dfe1e6;border-radius:3px;line-height:1.6}}.activity{{margin-top:30px}}.comment{{display:flex;gap:12px;padding:18px 0;border-top:1px solid #dfe1e6}}.avatar{{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;color:#fff;background:#6554c0;font-size:11px}}.details{{border:1px solid #dfe1e6;border-radius:3px}}.details h2{{margin:0;padding:16px;border-bottom:1px solid #dfe1e6}}dl{{display:grid;grid-template-columns:110px 1fr;margin:0;padding:10px 16px}}dt,dd{{padding:10px 0;margin:0}}dt{{color:#6b778c}}dd{{font-weight:500}}.status{{display:inline-block;padding:5px 8px;border-radius:3px;background:#deebff;color:#0747a6;font-size:11px;font-weight:700}}.status.done{{color:#006644;background:#e3fcef}}.status.blocked{{color:#bf2600;background:#ffebe6}}.return{{display:inline-block;margin-top:28px;color:#0052cc;text-decoration:none}}@media(max-width:760px){{.layout{{grid-template-columns:1fr}}aside{{display:none}}main{{padding:24px}}.content{{grid-template-columns:1fr}}.top nav{{display:none}}}}
    </style></head><body><header class='top'><span class='logo'>Jira Software</span><nav><span>Your work</span><span>Projects</span><span>Filters</span><span>Dashboards</span></nav><span class='search'>Search</span><span class='sim'>SIMULATED</span></header><div class='layout'><aside><strong>OPS Platform</strong><a>Summary</a><a class='active'>Issues</a><a>Board</a><a>Releases</a><a>Components</a></aside><main><div class='crumbs'>Projects / OPS Platform / {escape(issue.key)}</div><div class='head'><h1>{escape(issue.summary)}</h1><div><button>Edit</button> <button>Share</button></div></div><div class='content'><section><h2>Description</h2><div class='description'>Deliver this work for the monthly operations cycle. The record shown here is generated by Sync's Jira simulator and mirrors the fields used by the update workflow.<br><br><strong>Acceptance criteria</strong><ul><li>Implementation is reviewed and tested</li><li>Evidence is linked to the monthly update</li><li>Any blocker is recorded before the review cut-off</li></ul></div><div class='activity'><h2>Activity</h2><div class='comment'><span class='avatar'>{escape(assignee.avatar if assignee else '??')}</span><div><strong>{escape(assignee.name if assignee else issue.assignee)}</strong> updated the issue status<br><small>{escape(issue.updated_at)} · Linked from Sync</small></div></div></div><a class='return' href='http://localhost:5173'>← Return to Sync</a></section><aside class='details'><h2>Details</h2><dl><dt>Status</dt><dd><span class='status {status_class}'>{escape(issue.status)}</span></dd><dt>Assignee</dt><dd>{escape(assignee.name if assignee else issue.assignee)}</dd><dt>Due date</dt><dd>{escape(issue.due_date or 'None')}</dd><dt>Priority</dt><dd>Medium</dd><dt>Reporter</dt><dd>Weifa</dd><dt>Cycle</dt><dd>August 2026</dd><dt>Blocker</dt><dd>{escape(issue.blocked_reason or 'None')}</dd></dl></aside></div></main></div></body></html>""")


@app.get("/mock/git/commit/{sha}", response_class=HTMLResponse)
def mock_git(sha: str):
    commit = next((item for item in get_commits() if item.sha == sha), None)
    if not commit: raise HTTPException(status_code=404, detail="Commit not found")
    users = {user.id: user for user in get_users()}
    author = users.get(commit.author)
    safe_message = escape(commit.message)
    return HTMLResponse(f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>{escape(commit.sha)} · GitHub</title><style>
    *{{box-sizing:border-box}}body{{margin:0;color:#e6edf3;background:#0d1117;font:14px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}.top{{height:64px;display:flex;align-items:center;gap:20px;padding:0 28px;background:#010409;border-bottom:1px solid #30363d}}.cat{{font-size:30px}}.search{{width:280px;padding:8px 12px;color:#8b949e;border:1px solid #30363d;border-radius:6px}}.top nav{{display:flex;gap:16px;font-weight:600}}.sim{{margin-left:auto;padding:5px 8px;color:#0d1117;border-radius:20px;background:#f2cc60;font-size:10px;font-weight:700}}.repo-head{{padding:20px 32px 0;border-bottom:1px solid #21262d}}.repo{{font-size:20px;color:#58a6ff}}.repo span{{color:#8b949e}}.tabs{{display:flex;gap:24px;margin-top:20px}}.tabs b{{padding:12px 3px;border-bottom:2px solid #f78166}}main{{max-width:1160px;margin:auto;padding:32px}}.crumbs{{color:#8b949e;font-size:12px}}h1{{margin:14px 0 20px;font-size:24px;font-weight:500}}.commit-card{{border:1px solid #30363d;border-radius:6px;overflow:hidden}}.commit-meta{{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;background:#161b22}}.author{{display:flex;align-items:center;gap:10px}}.avatar{{display:grid;place-items:center;width:32px;height:32px;border-radius:50%;color:#0d1117;background:#58a6ff;font-size:11px;font-weight:700}}.sha{{padding:5px 8px;border:1px solid #30363d;border-radius:6px;font-family:ui-monospace,SFMono-Regular,monospace}}.summary{{display:flex;gap:22px;padding:13px 16px;border-top:1px solid #30363d;color:#8b949e}}.summary b{{color:#e6edf3}}.file{{margin-top:24px;border:1px solid #30363d;border-radius:6px;overflow:hidden}}.file-head{{display:flex;justify-content:space-between;padding:12px 16px;background:#161b22;font-family:ui-monospace,SFMono-Regular,monospace}}.diff{{width:100%;border-collapse:collapse;font:12px ui-monospace,SFMono-Regular,monospace}}.diff td{{padding:3px 10px}}.ln{{width:45px;color:#6e7681;text-align:right;border-right:1px solid #30363d}}.ctx{{background:#0d1117}}.add{{background:#033a16}}.del{{background:#67060c}}.return{{display:inline-block;margin-top:26px;color:#58a6ff;text-decoration:none}}@media(max-width:700px){{.top nav,.search{{display:none}}main{{padding:20px}}.commit-meta{{align-items:flex-start;flex-direction:column;gap:14px}}}}
    </style></head><body><header class='top'><span class='cat'>◉</span><span class='search'>Search or jump to…</span><nav><span>Pull requests</span><span>Issues</span><span>Marketplace</span><span>Explore</span></nav><span class='sim'>SIMULATED</span></header><div class='repo-head'><div class='repo'><span>ops-platform /</span> claims-service <small>Public</small></div><div class='tabs'><span>Code</span><span>Issues</span><span>Pull requests</span><b>Commits</b><span>Actions</span><span>Security</span></div></div><main><div class='crumbs'>claims-service / commit / {escape(commit.sha)}</div><h1>{safe_message}</h1><section class='commit-card'><div class='commit-meta'><div class='author'><span class='avatar'>{escape(author.avatar if author else '??')}</span><div><strong>{escape(author.name if author else commit.author)}</strong> committed on {escape(commit.committed_at)}<br><small>Linked to {escape(commit.issue_key)}</small></div></div><span class='sha'>{escape(commit.sha)}</span></div><div class='summary'><span><b>1</b> file changed</span><span style='color:#3fb950'>+12 additions</span><span style='color:#f85149'>−3 deletions</span></div></section><section class='file'><div class='file-head'><span>src/services/claims.py</span><span>Viewed</span></div><table class='diff'><tr class='ctx'><td class='ln'>41</td><td class='ln'>41</td><td> def validate_claim(payload):</td></tr><tr class='del'><td class='ln'>42</td><td class='ln'></td><td>-    return payload is not None</td></tr><tr class='add'><td class='ln'></td><td class='ln'>42</td><td>+    if payload is None:</td></tr><tr class='add'><td class='ln'></td><td class='ln'>43</td><td>+        raise ValidationError("Claim payload is required")</td></tr><tr class='add'><td class='ln'></td><td class='ln'>44</td><td>+    return validate_amount(payload.amount)</td></tr><tr class='ctx'><td class='ln'>43</td><td class='ln'>45</td><td> </td></tr><tr class='ctx'><td class='ln'>44</td><td class='ln'>46</td><td> def submit_claim(payload):</td></tr></table></section><a class='return' href='http://localhost:5173'>← Return to Sync</a></main></body></html>""")


@app.get("/api/activity")
def activity(_: User = Depends(current_user)): return {"commits": get_commits(), "pull_requests": get_pull_requests()}
