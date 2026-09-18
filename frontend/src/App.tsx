import { FormEvent, useEffect, useMemo, useState } from "react";
import { API_URL, api, setApiUser } from "./api";
import type { Category, Dashboard, DeveloperUpdate, Insight, MeetingWorkspace, UpdateItem, User } from "./types";

type Page = "updates" | "meeting" | "settings";

function EvidenceLinks({ evidence }: { evidence: UpdateItem["evidence"] }) {
  if (!evidence.length) return <span className="manual-tag">MANUAL ENTRY</span>;
  return <div className="evidence">{evidence.map((item) => <a key={item.reference} href={item.url ? `${API_URL}${item.url}` : "#"} target="_blank" rel="noreferrer"><span>{item.source === "git" ? "GH" : "J"}</span>{item.label}</a>)}</div>;
}

function TeamPulse({ dashboard, insights, updates }: { dashboard: Dashboard | null; insights: Insight[]; updates: DeveloperUpdate[] }) {
  if (!dashboard) return null;
  const ready = updates.filter((update) => update.approved).length;
  const stages = [
    { label: "Done", value: dashboard.completed, tone: "done" },
    { label: "Moving", value: dashboard.active, tone: "moving" },
    { label: "Blocked", value: dashboard.blocked, tone: "blocked" },
    { label: "Review", value: dashboard.open_reviews, tone: "review" },
  ];
  const total = Math.max(stages.reduce((sum, item) => sum + item.value, 0), 1);
  return <section className="team-pulse">
    <div className="pulse-lead"><span className="kicker">WEIFA'S TEAM VIEW · AUGUST</span><h1>Seven updates.<br /><em>One conversation.</em></h1><p>Work is pulled from GitHub, matched to Jira, then confirmed by the person who did it.</p></div>
    <div className="readiness-board"><div className="readiness-number"><strong>{ready}</strong><span>of {updates.length} ready</span></div><div className="readiness-rule"><i style={{ width: `${updates.length ? ready / updates.length * 100 : 0}%` }} /></div><small>Review closes 28 Aug · Meeting 31 Aug</small></div>
    <div className="flow-board"><div className="flow-title"><span>DELIVERY MIX</span><strong>{total} tracked signals</strong></div><div className="stacked-flow">{stages.map((stage) => <i className={stage.tone} style={{ width: `${stage.value / total * 100}%` }} key={stage.label} />)}</div><div className="flow-legend">{stages.map((stage) => <span key={stage.label}><i className={stage.tone} />{stage.label} <b>{stage.value}</b></span>)}</div></div>
    <div className="signal-board"><span className="kicker">NEEDS A LOOK</span>{insights.slice(0, 2).map((item) => <div className="signal-row" key={item.id}><i className={item.severity} /><div><strong>{item.title}</strong><p>{item.detail}</p></div><small>{item.evidence.join(" · ")}</small></div>)}</div>
  </section>;
}

function ItemEditor({ item, onSave, onCancel }: { item?: UpdateItem; onSave: (data: { title: string; detail: string; category: Category; target_date: string | null }) => void; onCancel: () => void }) {
  const [title, setTitle] = useState(item?.title ?? "");
  const [detail, setDetail] = useState(item?.detail ?? "");
  const [category, setCategory] = useState<Category>(item?.category ?? "in_progress");
  const [date, setDate] = useState(item?.target_date ?? "");
  function submit(event: FormEvent) { event.preventDefault(); onSave({ title, detail, category, target_date: date || null }); }
  return <div className="modal-backdrop"><form className="modal" onSubmit={submit}><span className="kicker">UPDATE ITEM</span><h2>{item ? "Edit the wording" : "Add something missing"}</h2><label>Short update<input value={title} onChange={(event) => setTitle(event.target.value)} required minLength={2} /></label><label>Context<textarea value={detail} onChange={(event) => setDetail(event.target.value)} rows={4} /></label><div className="form-row"><label>Section<select value={category} onChange={(event) => setCategory(event.target.value as Category)}><option value="completed">Completed</option><option value="in_progress">In progress</option><option value="blocker">Blocker</option></select></label><label>Target date<input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label></div><div className="modal-actions"><button type="button" className="quiet" onClick={onCancel}>Cancel</button><button type="submit">Save</button></div></form></div>;
}

function Updates({ updates, viewer, onRefresh }: { updates: DeveloperUpdate[]; viewer: User; onRefresh: () => Promise<void> }) {
  const [selectedId, setSelectedId] = useState("");
  const [editing, setEditing] = useState<UpdateItem | "new" | null>(null);
  useEffect(() => { if (!updates.some((item) => item.developer.id === selectedId)) setSelectedId(updates[0]?.developer.id ?? ""); }, [updates, selectedId]);
  const selected = updates.find((item) => item.developer.id === selectedId) ?? updates[0];
  const mayEdit = !!selected && (viewer.role === "pm" || viewer.id === selected.developer.id);
  async function save(data: { title: string; detail: string; category: Category; target_date: string | null }) { if (!selected) return; if (editing && editing !== "new") await api.editItem(editing.id, data); else await api.addItem(selected.developer.id, data); setEditing(null); await onRefresh(); }
  if (!selected) return <div className="loader">No update available.</div>;
  return <section className={updates.length > 1 ? "updates-layout" : "updates-layout solo"}>
    {updates.length > 1 && <aside className="roster"><span className="kicker">TEAM ROSTER</span>{updates.map((update, index) => <button key={update.developer.id} className={update.developer.id === selected.developer.id ? "roster-person active" : "roster-person"} onClick={() => setSelectedId(update.developer.id)}><span className="roster-index">0{index + 1}</span><span><strong>{update.developer.name}</strong><small>{update.approved ? "Ready" : `${update.suggestions.length} to review`}</small></span><i>{update.approved ? "●" : "○"}</i></button>)}</aside>}
    <div className="update-sheet">
      <header className="sheet-head"><div><span className="kicker">{viewer.role === "pm" ? "TEAM MEMBER" : "MY MONTHLY UPDATE"}</span><h1>{selected.developer.name}</h1><p>{selected.developer.title} · 01–31 August</p></div>{mayEdit && <div className="sheet-actions"><button className="quiet" onClick={() => setEditing("new")}>Add item</button><button onClick={async () => { await api.approveUpdate(selected.developer.id); await onRefresh(); }}>{selected.approved ? "Ready ✓" : "Submit update"}</button></div>}</header>
      {!!selected.suggestions.length && <section className="capture-strip"><div className="capture-count"><strong>{selected.suggestions.length}</strong><span>GitHub suggestions</span></div><div className="capture-list">{selected.suggestions.map((suggestion) => <article className="captured-item" key={suggestion.id}><div><span className="source-label">AUTO-CAPTURED</span><strong>{suggestion.title}</strong><p>{suggestion.detail}</p><EvidenceLinks evidence={suggestion.evidence} /></div>{mayEdit && <div className="capture-actions"><button onClick={async () => { await api.acceptSuggestion(suggestion.id); await onRefresh(); }}>Keep</button><button className="quiet" onClick={async () => { await api.dismissSuggestion(suggestion.id); await onRefresh(); }}>Ignore</button></div>}</article>)}</div></section>}
      <section className="ledger">{(["completed", "in_progress", "blocker"] as Category[]).map((category, column) => { const items = selected.items.filter((item) => item.category === category); return <div className="ledger-section" key={category}><header><span>0{column + 1}</span><h2>{category === "in_progress" ? "In progress" : category[0].toUpperCase() + category.slice(1)}</h2><b>{items.length}</b></header>{items.map((item) => <article className="ledger-item" key={item.id}><div className={`ledger-mark ${category}`} /><div className="ledger-copy"><strong>{item.title}</strong><p>{item.detail || "No additional context."}</p><EvidenceLinks evidence={item.evidence} /></div>{mayEdit && <div className="ledger-actions"><button onClick={() => setEditing(item)}>Edit</button><button onClick={async () => { await api.deleteItem(item.id); await onRefresh(); }}>Remove</button></div>}</article>)}{!items.length && <div className="ledger-empty">Nothing here yet.</div>}</div>; })}</section>
    </div>
    {editing && <ItemEditor item={editing === "new" ? undefined : editing} onSave={save} onCancel={() => setEditing(null)} />}
  </section>;
}

function Meeting({ workspace, viewer, onRefresh }: { workspace: MeetingWorkspace | null; viewer: User; onRefresh: () => Promise<void> }) {
  const [notes, setNotes] = useState("");
  useEffect(() => setNotes(workspace?.notes ?? ""), [workspace]);
  if (!workspace) return <div className="loader">Preparing meeting…</div>;
  const isPm = viewer.role === "pm";
  return <section className="meeting-page"><header className="meeting-head"><div><span className="kicker">31 AUG · MONTHLY SYNC</span><h1>The room where<br /><em>work becomes decisions.</em></h1></div><div className="meeting-ready"><strong>{workspace.approved_updates}/{workspace.total_updates}</strong><span>updates ready</span></div></header><div className="meeting-workspace"><article className="notes-sheet"><header><span className="kicker">LIVE NOTES</span>{isPm && <button className="quiet" onClick={async () => { await api.saveNotes(notes); await onRefresh(); }}>Save</button>}</header><textarea value={notes} onChange={(event) => setNotes(event.target.value)} disabled={!isPm} placeholder={isPm ? "Capture decisions, owners and dates…" : "Weifa records the meeting decisions here."} />{isPm && <button onClick={async () => { await api.saveNotes(notes); await api.suggestActions(); await onRefresh(); }}>Generate Jira proposals →</button>}</article><article className="action-sheet"><span className="kicker">PROPOSED, NOT APPLIED</span><h2>Jira actions</h2>{workspace.actions.map((action, index) => <div className="action-row" key={action.id}><span>0{index + 1}</span><div><strong>{action.title}</strong><small>{action.action.replace("_", " ")} · human approval required</small></div>{isPm && <button disabled={action.approved} onClick={async () => { await api.approveAction(action.id); await onRefresh(); }}>{action.approved ? "Approved" : "Approve"}</button>}</div>)}{!workspace.actions.length && <p className="no-actions">Meeting notes will become reviewable Jira proposals.</p>}</article></div></section>;
}

function Settings() {
  return <section className="settings-page"><header><span className="kicker">CONNECTIONS & CYCLE</span><h1>Quiet machinery.</h1><p>Simulated integrations use the same boundary as the future GitHub App and Jira OAuth connectors.</p></header><div className="connector-list"><article><span className="connector-logo github">GH</span><div><strong>GitHub · ops-platform</strong><p>8 repositories · commits and pull requests · read only</p></div><i>CONNECTED</i></article><article><span className="connector-logo jira">J</span><div><strong>Jira · OPS project</strong><p>Issues, status and due dates · simulated write approval</p></div><i>CONNECTED</i></article></div><div className="cycle-spec"><span>UPDATE WINDOW</span><strong>01 AUG</strong><i>→</i><span>REVIEW CUT-OFF</span><strong>28 AUG</strong><i>→</i><span>TEAM MEETING</span><strong>31 AUG</strong></div></section>;
}

function App() {
  const [page, setPage] = useState<Page>("updates");
  const [users, setUsers] = useState<User[]>([]);
  const [viewerId, setViewerId] = useState(localStorage.getItem("sync-user") ?? "bryan");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [updates, setUpdates] = useState<DeveloperUpdate[]>([]);
  const [meeting, setMeeting] = useState<MeetingWorkspace | null>(null);
  const [error, setError] = useState("");
  const viewer = useMemo(() => users.find((user) => user.id === viewerId) ?? users[0], [users, viewerId]);
  async function loadAll() { try { const [d, i, u, m] = await Promise.all([api.dashboard(), api.insights(), api.updates(), api.meeting()]); setDashboard(d); setInsights(i); setUpdates(u); setMeeting(m); setError(""); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not reach Sync API"); } }
  useEffect(() => { api.users().then(setUsers).catch(() => setError("Start FastAPI on port 8000.")); void loadAll(); }, []);
  async function changeUser(id: string) { setViewerId(id); setApiUser(id); setPage("updates"); await loadAll(); }
  const nav: [Page, string][] = viewer?.role === "pm" ? [["updates", "Team updates"], ["meeting", "Meeting"], ["settings", "Settings"]] : [["updates", "My update"], ["meeting", "Meeting summary"]];
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-mark">S/</div><span>sync</span></div><div className="rail-label">MONTHLY DELIVERY LOG</div><nav>{nav.map(([id, label], index) => <button className={page === id ? "active" : ""} key={id} onClick={() => setPage(id)}><span>0{index + 1}</span>{label}</button>)}</nav><div className="systems"><span><i className="gh-dot" />GitHub</span><span><i className="jira-dot" />Jira</span><small>SIMULATION ONLINE</small></div></aside><main className="main"><header className="app-header"><div className="cycle-track"><span>01 AUG</span><i /><span>28 AUG · REVIEW</span><i /><strong>31 AUG · MEETING</strong></div><div className="user-switch"><span>{viewer?.role === "pm" ? "PM VIEW" : "DEVELOPER VIEW"}</span><div className="avatar">{viewer?.avatar ?? "…"}</div><select value={viewerId} onChange={(event) => void changeUser(event.target.value)}>{users.map((user) => <option value={user.id} key={user.id}>{user.name} · {user.role.toUpperCase()}</option>)}</select></div></header><div className="content">{error && <div className="error">{error}</div>}{page === "updates" && viewer && <>{viewer.role === "pm" && <TeamPulse dashboard={dashboard} insights={insights} updates={updates} />}<Updates updates={updates} viewer={viewer} onRefresh={loadAll} /></>}{page === "meeting" && viewer && <Meeting workspace={meeting} viewer={viewer} onRefresh={loadAll} />}{page === "settings" && <Settings />}</div></main></div>;
}

export default App;
