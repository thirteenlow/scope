import { useEffect, useState } from "react";
import "./App.css";

type HealthResponse = {
  status: string;
};

function App() {
  const [backendStatus, setBackendStatus] = useState("Checking...");

  useEffect(() => {
    async function checkBackend() {
      try {
        const apiUrl =
          import.meta.env.VITE_API_URL ?? "http://localhost:8000";

        const response = await fetch(`${apiUrl}/health`);

        if (!response.ok) {
          throw new Error("Backend request failed");
        }

        const data: HealthResponse = await response.json();
        setBackendStatus(data.status);
      } catch {
        setBackendStatus("Unavailable");
      }
    }

    checkBackend();
  }, []);

  return (
    <main className="page">
      <div className="container">
        <header>
          <p className="brand">sync</p>
          <h1>Team activity, summarized.</h1>
          <p className="subtitle">
            See what moved, what is blocked, and what needs attention.
          </p>
        </header>

        <section className="status-card">
          <span>Backend status</span>
          <strong>{backendStatus}</strong>
        </section>
      </div>
    </main>
  );
}

export default App;