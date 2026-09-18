import { useEffect, useState } from "react";
import { api } from "./api";
import type { Dashboard, DeveloperUpdate, MeetingReport, WorkItem } from "./types";

function ItemList({ items, empty }: { items: WorkItem[]; empty: string }) {
  if (items.length === 0) return <p className="empty">{empty}</p>;
  return (
    <ul className="item-list">
      {items.map((item) => (
        <li key={item.issue_key}>
          <div><strong>{item.issue_key}</strong> {item.summary}</div>
          <small>{item.evidence.map((e) => e.reference).join(" · ")}</small>
        </li>
      ))}
    </ul>
  );
}

function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [updates, setUpdates] = useState<DeveloperUpdate[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [report, setReport] = useState<MeetingReport | null>(null);
  const [error, setError] = useState("");

  async function refresh() {
    try {
      const [dashboardData, updateData] = await Promise.all([
        api.dashboard(),
        api.updates(),
      ]);
      setDashboard(dashboardData);
      setUpdates(updateData);
      setSelectedId((current) => current || updateData[0]?.developer_id || "");
      setError("");
    } catch {
      setError("Could not reach the Sync API. Confirm FastAPI is running on port 8000.");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const selected = updates.find((update) => update.developer_id === selectedId);

  async function approve() {
    if (!selected) return;
    await api.approve(selected.developer_id);
    await refresh();
  }

  async function generateReport() {
    setReport(await api.report());
  }

  return (
    <main>
      <header className="topbar">
        <div><span className="logo">sync</span><span className="period">August 2026</span></div>
        <button className="secondary" onClick={generateReport}>Generate meeting report</button>
      </header>

      <div className="shell">
        <section className="hero">
          <p>Team overview</p>
          <h1>Know what moved, what’s blocked, and what needs attention.</h1>
        </section>

        {error && <p className="error">{error}</p>}

        {dashboard && (
          <section className="metrics" aria-label="Team metrics">
            <article><span>Completed</span><strong>{dashboard.completed}</strong></article>
            <article><span>Active</span><strong>{dashboard.active}</strong></article>
            <article><span>Blocked</span><strong>{dashboard.blocked}</strong></article>
            <article><span>Stale</span><strong>{dashboard.stale}</strong></article>
            <article><span>Open reviews</span><strong>{dashboard.open_reviews}</strong></article>
          </section>
        )}

        <section className="workspace">
          <aside>
            <h2>Developer updates</h2>
            {updates.map((update) => (
              <button
                className={update.developer_id === selectedId ? "person selected" : "person"}
                key={update.developer_id}
                onClick={() => setSelectedId(update.developer_id)}
              >
                <span>{update.developer_name}</span>
                <small>{update.approved ? "Approved" : "Needs review"}</small>
              </button>
            ))}
          </aside>

          {selected && (
            <article className="update">
              <div className="update-header">
                <div><p>Monthly update</p><h2>{selected.developer_name}</h2></div>
                <button disabled={selected.approved} onClick={approve}>
                  {selected.approved ? "Approved" : "Approve update"}
                </button>
              </div>
              <div className="update-grid">
                <section><h3>Completed</h3><ItemList items={selected.completed} empty="No completed items." /></section>
                <section><h3>In progress</h3><ItemList items={selected.in_progress} empty="No active items." /></section>
                <section><h3>Blockers</h3><ItemList items={selected.blockers} empty="No blockers recorded." /></section>
                <section><h3>Needs attention</h3><ItemList items={selected.needs_attention} empty="Nothing requires attention." /></section>
              </div>
            </article>
          )}
        </section>

        {report && (
          <section className="report">
            <div><p>Meeting brief</p><h2>{report.month}</h2></div>
            <p>{report.approved_updates} approved developer update(s) included.</p>
            <div className="report-grid">
              <div><h3>Achievements</h3><ul>{report.achievements.map((x) => <li key={x}>{x}</li>)}</ul></div>
              <div><h3>Blockers</h3><ul>{report.blockers.map((x) => <li key={x}>{x}</li>)}</ul></div>
              <div><h3>Decisions</h3><ul>{report.decisions_needed.map((x) => <li key={x}>{x}</li>)}</ul></div>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

export default App;

