import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "./api";
import {
  ArrowIcon,
  CheckIcon,
  CodeIcon,
  FileIcon,
  FolderIcon,
  GitIcon,
  JiraIcon,
  LayersIcon,
  SearchIcon,
  SparkIcon,
} from "./icons";
import type {
  Analysis,
  Bootstrap,
  ChatMessage,
  ConversationSummary,
  JiraIssue,
  LlmStatus,
  ProductFeature,
  RepoFile,
  RepoNode,
  ScopeOption,
  Screen,
} from "./types";

const starterMessage: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi Person — I’m connected to the PocketPlan codebase. Tell me what you want to build for individual budgeters and the delivery window. I’ll ask only the questions that materially change the plan.",
  createdAt: "Now",
};
type Drawer = "artifact" | "code" | null;

const LAST_CONVERSATION_KEY = "scope:lastConversationId";

function newId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function")
    return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function relativeTime(value: string): string {
  const elapsed = Date.now() - new Date(value).getTime();
  if (elapsed < 60_000) return "Just now";
  if (elapsed < 3_600_000) return `${Math.floor(elapsed / 60_000)}m ago`;
  if (elapsed < 86_400_000) return `${Math.floor(elapsed / 3_600_000)}h ago`;
  if (elapsed < 604_800_000) return `${Math.floor(elapsed / 86_400_000)}d ago`;
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export default function App() {
  const [data, setData] = useState<Bootstrap | null>(null);
  const [status, setStatus] = useState<LlmStatus | null>(null);
  const [screen, setScreen] = useState<Screen>("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([starterMessage]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [productFeatures, setProductFeatures] = useState<ProductFeature[]>([]);
  const [input, setInput] = useState("");
  const [weeks, setWeeks] = useState<number | null>(4);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [prd, setPrd] = useState<string | null>(null);
  const [prdModel, setPrdModel] = useState<string | null>(null);
  const [jiraSyncedAt, setJiraSyncedAt] = useState<string | null>(null);
  const [jiraIssueKeys, setJiraIssueKeys] = useState<string[]>([]);
  const [jira, setJira] = useState<JiraIssue[]>([]);
  const [tree, setTree] = useState<RepoNode[]>([]);
  const [file, setFile] = useState<RepoFile | null>(null);
  const [busy, setBusy] = useState<
    "chat" | "plan" | "prd" | "jira" | "load" | ""
  >("");
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [drawer, setDrawer] = useState<Drawer>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadInitialData() {
      try {
        const [bootstrap, repoTree, llm, history, catalogue] =
          await Promise.all([
            api.bootstrap(),
            api.tree(),
            api.llmStatus(),
            api.conversations(),
            api.productFeatures(),
          ]);
        if (cancelled) return;
        setData(bootstrap);
        setJira(bootstrap.jira);
        setTree(repoTree);
        setStatus(llm);
        setConversations(history);
        setProductFeatures(catalogue);
        const lastId = localStorage.getItem(LAST_CONVERSATION_KEY);
        if (lastId && history.some((item) => item.id === lastId))
          void openConversation(lastId);
      } catch (err) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Unable to load Scope");
      }
    }
    void loadInitialData();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);
  const userMessages = messages.filter(
    (message) => message.role === "user",
  ).length;
  async function refreshConversations() {
    setConversations(await api.conversations());
  }

  async function send(mode: "chat" | "plan", suggested?: string) {
    if (busy) return;
    const text = (suggested ?? input).trim();
    let next = messages;
    if (text) {
      next = [
        ...messages,
        { id: newId(), role: "user", content: text, createdAt: "Now" },
      ];
      setMessages(next);
      setInput("");
    }
    if (next.every((message) => message.role !== "user")) return;
    setBusy(mode);
    setError("");
    try {
      const result = await api.chat(next, mode, weeks, conversationId);
      setConversationId(result.conversation_id);
      localStorage.setItem(LAST_CONVERSATION_KEY, result.conversation_id);
      setMessages((current) => [
        ...current,
        {
          id: newId(),
          role: "assistant",
          content: result.message,
          createdAt: "Now",
        },
      ]);
      if (result.analysis) {
        const recommended =
          result.analysis.options.find((option) => option.recommended)?.id ||
          result.analysis.options[0]?.id ||
          null;
        setAnalysis(result.analysis);
        setSelectedOption(recommended);
        setPrd(null);
        setPrdModel(null);
        setJiraSyncedAt(null);
        setJiraIssueKeys([]);
        setDrawer("artifact");
      }
      await refreshConversations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Claude request failed");
    } finally {
      setBusy("");
    }
  }

  async function openConversation(id: string) {
    setBusy("load");
    setError("");
    try {
      const saved = await api.conversation(id);
      setConversationId(saved.id);
      localStorage.setItem(LAST_CONVERSATION_KEY, saved.id);
      setMessages([
        starterMessage,
        ...saved.messages.map((message) => ({
          id: message.id,
          role: message.role,
          content: message.content,
          createdAt: relativeTime(message.created_at),
        })),
      ]);
      setWeeks(saved.target_weeks);
      setAnalysis(saved.analysis);
      setSelectedOption(
        saved.selected_option ||
          saved.analysis?.options.find((option) => option.recommended)?.id ||
          saved.analysis?.options[0]?.id ||
          null,
      );
      setPrd(saved.prd_markdown);
      setPrdModel(saved.prd_model);
      setJiraSyncedAt(saved.jira_synced_at);
      setJiraIssueKeys(saved.jira_issue_keys);
      setDrawer(null);
      setScreen("chat");
      setSidebarOpen(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to open conversation",
      );
    } finally {
      setBusy("");
    }
  }

  async function removeConversation(id: string) {
    try {
      await api.deleteConversation(id);
      if (conversationId === id) newChat();
      await refreshConversations();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to delete conversation",
      );
    }
  }

  async function chooseOption(optionId: string) {
    if (optionId !== selectedOption) {
      setJiraSyncedAt(null);
      setJiraIssueKeys([]);
    }
    setSelectedOption(optionId);
    setPrd(null);
    setPrdModel(null);
    if (!conversationId) return;
    try {
      await api.selectOption(conversationId, optionId);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to save scope choice",
      );
    }
  }

  async function createPrd() {
    if (!conversationId || !selectedOption) return;
    setBusy("prd");
    setError("");
    try {
      const result = await api.generatePrd(conversationId, selectedOption);
      setPrd(result.markdown);
      setPrdModel(result.model);
      await refreshConversations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "PRD generation failed");
    } finally {
      setBusy("");
    }
  }

  async function createJira() {
    if (!analysis || !selectedOption || !conversationId) return;
    setBusy("jira");
    setError("");
    try {
      const created = await api.syncConversationJira(
        conversationId,
        selectedOption,
      );
      setJiraSyncedAt(new Date().toISOString());
      setJiraIssueKeys(created.map((issue) => issue.key));
      setJira(await api.jira());
      setMessages((current) => [
        ...current,
        {
          id: newId(),
          role: "assistant",
          content: `Done — ${created.length} approved work items were created in the PocketPlan Jira backlog.`,
          createdAt: "Now",
        },
      ]);
      setDrawer(null);
      setScreen("jira");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Jira sync failed");
    } finally {
      setBusy("");
    }
  }

  async function openFile(path: string) {
    try {
      setFile(await api.file(path));
      setDrawer("code");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to open repository file",
      );
    }
  }

  function newChat() {
    localStorage.removeItem(LAST_CONVERSATION_KEY);
    setMessages([starterMessage]);
    setConversationId(null);
    setAnalysis(null);
    setSelectedOption(null);
    setPrd(null);
    setPrdModel(null);
    setJiraSyncedAt(null);
    setJiraIssueKeys([]);
    setInput("");
    setDrawer(null);
    setScreen("chat");
    setSidebarOpen(false);
  }
  function navigate(next: Screen) {
    setScreen(next);
    setDrawer(null);
    setSidebarOpen(false);
  }
  function planFromFeature(feature?: ProductFeature) {
    newChat();
    setInput(
      feature
        ? `I want to enhance the existing “${feature.name}” feature. Current capability: ${feature.summary} It already supports ${feature.capabilities.join(", ")}. Help me define the improvement and assess it against the codebase.`
        : "I want to add a new feature to PocketPlan: ",
    );
  }

  if (!data || !status)
    return (
      <div className="loading">
        <div className="logo">S/</div>
        <span>Connecting product context…</span>
      </div>
    );

  return (
    <div className={`app ${sidebarCollapsed ? "collapsed" : ""}`}>
      {sidebarOpen && (
        <button
          className="scrim"
          aria-label="Close menu"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <Sidebar
        data={data}
        status={status}
        screen={screen}
        open={sidebarOpen}
        collapsed={sidebarCollapsed}
        conversations={conversations}
        activeConversation={conversationId}
        close={() => setSidebarOpen(false)}
        toggle={() => setSidebarCollapsed((value) => !value)}
        newChat={newChat}
        navigate={navigate}
        openConversation={openConversation}
        removeConversation={removeConversation}
        openRepo={() => {
          setFile(null);
          setDrawer("code");
          setSidebarOpen(false);
        }}
      />
      <main className="workspace">
        <Header
          data={data}
          status={status}
          screen={screen}
          openMenu={() => setSidebarOpen(true)}
          openArtifact={() => setDrawer("artifact")}
        />
        {!status.configured && <ConfigBanner />}
        {error && (
          <div className="error-banner">
            <span>!</span>
            <p>{error}</p>
            <button onClick={() => setError("")}>×</button>
          </div>
        )}
        {screen === "chat" && (
          <>
            <section className="conversation">
              <div className="chat-width">
                <div className="conversation-head">
                  <span className="kicker">FEATURE PLANNING SESSION</span>
                  <h1>
                    {conversationId
                      ? conversations.find((item) => item.id === conversationId)
                          ?.title || "Continue the plan"
                      : "What should PocketPlan do next?"}
                  </h1>
                  <p>
                    Plan features for individuals who want clarity and control
                    over their personal budget.
                  </p>
                </div>
                <div className="messages">
                  {messages.map((message, index) => (
                    <Message
                      key={message.id}
                      message={message}
                      model={status.model}
                      last={index === messages.length - 1}
                    />
                  ))}
                  {busy && busy !== "load" && <Thinking mode={busy} />}
                  <div ref={endRef} />
                </div>
                {userMessages === 0 && (
                  <div className="prompts">
                    <Prompt
                      n="01"
                      title="Category rollover"
                      text="Carry unused money into next month"
                      onClick={() =>
                        send(
                          "chat",
                          "Allow users to carry unused category money into the next month. We need it within four weeks.",
                        )
                      }
                    />
                    <Prompt
                      n="02"
                      title="Smart categorization"
                      text="Create rules from transaction history"
                      onClick={() =>
                        send(
                          "chat",
                          "Suggest categories for imported transactions based on a user's previous choices.",
                        )
                      }
                    />
                    <Prompt
                      n="03"
                      title="Savings goals"
                      text="Plan progress toward personal targets"
                      onClick={() =>
                        send(
                          "chat",
                          "Let users create savings goals with a target date and suggested monthly contribution.",
                        )
                      }
                    />
                  </div>
                )}
              </div>
            </section>
            <Composer
              input={input}
              setInput={setInput}
              weeks={weeks}
              setWeeks={setWeeks}
              send={() => send("chat")}
              generate={() => send("plan")}
              disabled={!status.configured || Boolean(busy)}
              canGenerate={userMessages > 0}
            />
          </>
        )}
        {screen === "features" && (
          <FeatureCatalogue
            features={productFeatures}
            planFromFeature={planFromFeature}
          />
        )}
        {screen === "jira" && <JiraBacklog issues={jira} team={data.team} />}
      </main>
      <ContextDrawer
        drawer={drawer}
        close={() => setDrawer(null)}
        analysis={analysis}
        selectedOption={selectedOption}
        setSelectedOption={chooseOption}
        prd={prd}
        prdModel={prdModel}
        jiraSyncedAt={jiraSyncedAt}
        jiraIssueKeys={jiraIssueKeys}
        createPrd={createPrd}
        createJira={createJira}
        viewJira={() => {
          setDrawer(null);
          setScreen("jira");
        }}
        busy={busy}
        tree={tree}
        file={file}
        clearFile={() => setFile(null)}
        openFile={openFile}
        weeks={weeks}
      />
    </div>
  );
}

function Sidebar({
  data,
  status,
  screen,
  open,
  collapsed,
  conversations,
  activeConversation,
  close,
  toggle,
  newChat,
  navigate,
  openConversation,
  removeConversation,
  openRepo,
}: {
  data: Bootstrap;
  status: LlmStatus;
  screen: Screen;
  open: boolean;
  collapsed: boolean;
  conversations: ConversationSummary[];
  activeConversation: string | null;
  close: () => void;
  toggle: () => void;
  newChat: () => void;
  navigate: (screen: Screen) => void;
  openConversation: (id: string) => void;
  removeConversation: (id: string) => void;
  openRepo: () => void;
}) {
  return (
    <aside
      className={`sidebar ${open ? "mobile-open" : ""} ${collapsed ? "is-collapsed" : ""}`}
    >
      <div className="brand">
        <div className="logo">S/</div>
        <div className="brand-copy">
          <strong>scope</strong>
          <span>product intelligence</span>
        </div>
        <button className="close-mobile" onClick={close}>
          ×
        </button>
      </div>
      <button className="new-chat" onClick={newChat}>
        <span>＋</span>
        <b>New feature</b>
      </button>
      <nav className="side-section primary-nav">
        <label>WORKSPACE</label>
        <button
          className={screen === "chat" ? "active" : ""}
          onClick={() => navigate("chat")}
        >
          <SparkIcon />
          <span>
            <strong>Plan with AI</strong>
            <small>Code-aware discovery</small>
          </span>
        </button>
        <button
          className={screen === "features" ? "active" : ""}
          onClick={() => navigate("features")}
        >
          <LayersIcon />
          <span>
            <strong>Product features</strong>
            <small>Current capability map</small>
          </span>
        </button>
        <button
          className={screen === "jira" ? "active" : ""}
          onClick={() => navigate("jira")}
        >
          <JiraIcon />
          <span>
            <strong>Jira backlog</strong>
            <small>{data.jira.length} linked issues</small>
          </span>
        </button>
      </nav>
      <div className="side-section recent-section">
        <label>RECENT CHATS</label>
        {conversations.length === 0 && (
          <p className="empty-recents">
            Your saved planning chats appear here.
          </p>
        )}
        {conversations.slice(0, 8).map((item) => (
          <div
            className={`recent-row ${activeConversation === item.id && screen === "chat" ? "active" : ""}`}
            key={item.id}
          >
            <button
              className="recent-open"
              onClick={() => openConversation(item.id)}
            >
              <FileIcon />
              <span>
                <strong>{item.title}</strong>
                <small>
                  {relativeTime(item.updated_at)}
                  {item.has_plan ? " · plan" : ""}
                </small>
              </span>
            </button>
            <button
              className="recent-delete"
              title="Delete chat"
              aria-label={`Delete ${item.title}`}
              onClick={() => removeConversation(item.id)}
            >
              ×
            </button>
          </div>
        ))}
      </div>
      <div className="side-section connections">
        <label>CONNECTIONS</label>
        <button onClick={openRepo}>
          <GitIcon />
          <span>
            <strong>{data.repository.name}</strong>
            <small>
              <i /> {data.repository.files} files indexed
            </small>
          </span>
        </button>
        <button onClick={() => navigate("jira")}>
          <JiraIcon />
          <span>
            <strong>PocketPlan Jira</strong>
            <small>
              <i /> Mock project connected
            </small>
          </span>
        </button>
        <button>
          <SparkIcon />
          <span>
            <strong>Claude</strong>
            <small>
              <i className={status.configured ? "" : "off"} />{" "}
              {status.configured ? status.model : "Setup required"}
            </small>
          </span>
        </button>
      </div>
      <div className="side-footer">
        <div className="avatar">W</div>
        <span>
          <strong>Person</strong>
          <small>PM</small>
        </span>
        <button
          className="collapse-button"
          onClick={toggle}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? "›" : "‹"}
        </button>
      </div>
    </aside>
  );
}

function Header({
  data,
  status,
  screen,
  openMenu,
  openArtifact,
}: {
  data: Bootstrap;
  status: LlmStatus;
  screen: Screen;
  openMenu: () => void;
  openArtifact: () => void;
}) {
  return (
    <header className="header">
      <button className="menu-button" onClick={openMenu}>
        ☰
      </button>
      <div className="repo-chip">
        <GitIcon />
        <span>{data.repository.name}</span>
        <b>{data.repository.branch}</b>
      </div>
      <div className="context-status">
        <span />
        <p>
          <strong>
            {screen === "features"
              ? "Product capability map"
              : screen === "jira"
                ? "Delivery workspace"
                : "Code context ready"}
          </strong>
          <small>{data.repository.commit} · indexed</small>
        </p>
      </div>
      <div className="header-right">
        <span className={`model-status ${status.configured ? "" : "offline"}`}>
          <SparkIcon />
          {status.configured ? status.model : "Claude offline"}
        </span>
        {screen === "chat" && (
          <button className="mobile-plan" onClick={openArtifact}>
            <LayersIcon />
            <span>Plan</span>
          </button>
        )}
        <div className="team">
          {data.team.slice(0, 3).map((member) => (
            <i key={member.name}>{member.initials}</i>
          ))}
        </div>
      </div>
    </header>
  );
}
function Message({
  message,
  model,
  last,
}: {
  message: ChatMessage;
  model: string;
  last: boolean;
}) {
  if (message.role === "user")
    return (
      <article className="message user-message">
        <div className="avatar">W</div>
        <div>
          <div className="message-meta">
            <strong>You</strong>
            <span>{message.createdAt}</span>
          </div>
          <p>{message.content}</p>
        </div>
      </article>
    );
  return (
    <article className={`message assistant-message ${last ? "latest" : ""}`}>
      <div className="ai-avatar">
        <SparkIcon />
      </div>
      <div>
        <div className="message-meta">
          <strong>Scope</strong>
          <span>{model}</span>
        </div>
        <div className="message-body markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </article>
  );
}
function Thinking({ mode }: { mode: string }) {
  return (
    <article className="message assistant-message">
      <div className="ai-avatar">
        <SparkIcon />
      </div>
      <div>
        <div className="message-meta">
          <strong>Scope</strong>
          <span>working</span>
        </div>
        <div className="thinking">
          <i />
          <i />
          <i />
          <span>
            {mode === "plan"
              ? "Tracing the request through the codebase and building a plan…"
              : mode === "prd"
                ? "Writing the full PRD from the selected scope…"
                : mode === "jira"
                  ? "Creating Jira work items…"
                  : "Reading the product context…"}
          </span>
        </div>
      </div>
    </article>
  );
}
function Prompt({
  n,
  title,
  text,
  onClick,
}: {
  n: string;
  title: string;
  text: string;
  onClick: () => void;
}) {
  return (
    <button onClick={onClick}>
      <span>{n}</span>
      <p>
        <strong>{title}</strong>
        {text}
      </p>
      <ArrowIcon />
    </button>
  );
}
function Composer({
  input,
  setInput,
  weeks,
  setWeeks,
  send,
  generate,
  disabled,
  canGenerate,
}: {
  input: string;
  setInput: (value: string) => void;
  weeks: number | null;
  setWeeks: (value: number | null) => void;
  send: () => void;
  generate: () => void;
  disabled: boolean;
  canGenerate: boolean;
}) {
  return (
    <div className="composer-wrap">
      <div className="composer">
        <textarea
          rows={2}
          placeholder="Describe the feature, answer a question, or change the scope…"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
              event.preventDefault();
              send();
            }
          }}
        />
        <div className="composer-tools">
          <div className="timeline">
            <span>Target</span>
            {weeks !== null ? (
              <>
                <button onClick={() => setWeeks(Math.max(1, weeks - 1))}>−</button>
                <strong>{weeks} week{weeks === 1 ? "" : "s"}</strong>
                <button onClick={() => setWeeks(Math.min(52, weeks + 1))}>＋</button>
                <button
                  className="timeline-clear-btn"
                  onClick={() => setWeeks(null)}
                  title="Let Scope estimate the timeline instead"
                >
                  or estimate
                </button>
              </>
            ) : (
              <>
                <span className="timeline-estimate-label">Scope will estimate</span>
                <button
                  className="timeline-set-btn"
                  onClick={() => setWeeks(4)}
                >
                  set target
                </button>
              </>
            )}
          </div>
          <div className="composer-actions">
            <button
              className="generate"
              onClick={generate}
              disabled={disabled || !canGenerate}
            >
              <SparkIcon />
              Generate plan
            </button>
            <button
              className="send"
              onClick={send}
              disabled={disabled || !input.trim()}
              aria-label="Send"
            >
              <ArrowIcon />
            </button>
          </div>
        </div>
      </div>
      <small>
        Enter for a new line · Ctrl/Cmd + Enter to send · Engineering should
        verify code evidence.
      </small>
    </div>
  );
}
function ConfigBanner() {
  return (
    <div className="config-banner">
      <span>Claude is not configured</span>
      <p>
        Add <code>ANTHROPIC_AUTH_TOKEN</code> and{" "}
        <code>ANTHROPIC_BASE_URL</code> to <code>backend/.env</code>, then
        restart FastAPI.
      </p>
    </div>
  );
}

function FeatureCatalogue({
  features,
  planFromFeature,
}: {
  features: ProductFeature[];
  planFromFeature: (feature?: ProductFeature) => void;
}) {
  return (
    <section className="features-page">
      <div className="page-intro">
        <span className="kicker">PRODUCT CAPABILITY MAP</span>
        <h1>What PocketPlan already does</h1>
        <p>
          Start with an existing capability when planning an enhancement, so
          Scope can ground the conversation in the right code and product
          behavior.
        </p>
        <div className="catalogue-stats">
          <span>
            <strong>{features.length}</strong> live features
          </span>
          <span>
            <strong>
              {features.reduce(
                (total, item) => total + item.capabilities.length,
                0,
              )}
            </strong>{" "}
            mapped capabilities
          </span>
          <span>
            <strong>100%</strong> code-linked
          </span>
        </div>
      </div>
      <div className="feature-grid">
        {features.map((feature) => (
          <article
            className={`feature-card ${feature.accent}`}
            key={feature.id}
          >
            <div className="feature-card-top">
              <span>{feature.category}</span>
              <b>● {feature.status}</b>
            </div>
            <div className="feature-glyph">
              <LayersIcon />
            </div>
            <h2>{feature.name}</h2>
            <p>{feature.summary}</p>
            <div className="capability-list">
              {feature.capabilities.map((capability) => (
                <span key={capability}>
                  <CheckIcon />
                  {capability}
                </span>
              ))}
            </div>
            <div className="feature-evidence">
              <GitIcon />
              <span>{feature.evidence_paths.length} code references</span>
            </div>
            <button onClick={() => planFromFeature(feature)}>
              Enhance this feature <ArrowIcon />
            </button>
          </article>
        ))}
        <button
          className="feature-card add-feature"
          onClick={() => planFromFeature()}
        >
          <span>＋</span>
          <h2>Propose something new</h2>
          <p>
            Open a fresh code-aware conversation and turn an early idea into a
            feasible product plan.
          </p>
          <b>
            Plan with Scope <ArrowIcon />
          </b>
        </button>
      </div>
    </section>
  );
}

function JiraBacklog({
  issues,
  team,
}: {
  issues: JiraIssue[];
  team: Bootstrap["team"];
}) {
  const [query, setQuery] = useState("");
  const filtered = issues.filter((issue) =>
    `${issue.key} ${issue.summary} ${issue.labels.join(" ")}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  const sprint = filtered.filter((issue) =>
    ["In Progress", "In Review", "Done"].includes(issue.status),
  );
  const backlog = filtered.filter((issue) => !sprint.includes(issue));
  return (
    <section className="jira-app">
      <aside className="jira-project-nav">
        <div className="jira-project-mark">PP</div>
        <div>
          <strong>PocketPlan</strong>
          <span>Software project</span>
        </div>
        <nav>
          <button>Roadmap</button>
          <button className="active">Backlog</button>
          <button>Board</button>
          <button>Releases</button>
          <button>Reports</button>
          <button>Project settings</button>
        </nav>
      </aside>
      <main className="jira-main">
        <div className="jira-breadcrumb">Projects / PocketPlan</div>
        <div className="jira-title-row">
          <div>
            <h1>Backlog</h1>
            <p>Plan and prioritise work for the PocketPlan team.</p>
          </div>
          <button className="jira-create">Create</button>
        </div>
        <div className="jira-toolbar">
          <label>
            <SearchIcon />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search backlog"
            />
          </label>
          <div className="jira-avatars">
            {team.slice(0, 6).map((member) => (
              <i title={member.name} key={member.name}>
                {member.initials}
              </i>
            ))}
          </div>
          <button>Epic</button>
          <button>Label</button>
          <button>⋯</button>
        </div>
        <BacklogGroup
          title="POCKETPLAN SPRINT 24"
          subtitle={`${sprint.length} issues · 13 story points`}
          issues={sprint}
          action="Start sprint"
        />
        <BacklogGroup
          title="BACKLOG"
          subtitle={`${backlog.length} issues`}
          issues={backlog}
          action="Create sprint"
        />
        <button className="jira-add">＋ Create issue</button>
      </main>
    </section>
  );
}
function BacklogGroup({
  title,
  subtitle,
  issues,
  action,
}: {
  title: string;
  subtitle: string;
  issues: JiraIssue[];
  action: string;
}) {
  return (
    <section className="backlog-group">
      <header>
        <span>⌄</span>
        <strong>{title}</strong>
        <small>{subtitle}</small>
        <button>{action}</button>
      </header>
      <div className="backlog-list">
        {issues.length === 0 ? (
          <p className="empty-backlog">No matching issues</p>
        ) : (
          issues.map((issue) => <JiraRow key={issue.key} issue={issue} />)
        )}
      </div>
    </section>
  );
}
function JiraRow({ issue }: { issue: JiraIssue }) {
  const icon =
    issue.type === "Story"
      ? "◆"
      : issue.type === "Epic"
        ? "⚡"
        : issue.type === "Spike"
          ? "◇"
          : "✓";
  return (
    <article className="jira-row">
      <span className={`jira-type ${issue.type.toLowerCase()}`}>{icon}</span>
      <a>{issue.key}</a>
      <strong>{issue.summary}</strong>
      {issue.labels.includes("scope-generated") && <em>Scope</em>}
      <div className="jira-labels">
        {issue.labels.slice(0, 2).map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>
      <b>{issue.estimate || "–"}</b>
      <i>
        {issue.assignee
          ? issue.assignee
              .split(" ")
              .map((part) => part[0])
              .join("")
          : "?"}
      </i>
      <small>{issue.status}</small>
    </article>
  );
}

function ContextDrawer({
  drawer,
  close,
  analysis,
  selectedOption,
  setSelectedOption,
  prd,
  prdModel,
  jiraSyncedAt,
  jiraIssueKeys,
  createPrd,
  createJira,
  viewJira,
  busy,
  tree,
  file,
  clearFile,
  openFile,
  weeks,
}: {
  drawer: Drawer;
  close: () => void;
  analysis: Analysis | null;
  selectedOption: string | null;
  setSelectedOption: (value: string) => void;
  prd: string | null;
  prdModel: string | null;
  jiraSyncedAt: string | null;
  jiraIssueKeys: string[];
  createPrd: () => void;
  createJira: () => void;
  viewJira: () => void;
  busy: string;
  tree: RepoNode[];
  file: RepoFile | null;
  clearFile: () => void;
  openFile: (path: string) => void;
  weeks: number | null;
}) {
  if (!drawer) return null;
  return (
    <>
      <button className="drawer-scrim" onClick={close} />
      <aside className="context-drawer">
        <div className="drawer-head">
          <div>
            <span>
              {drawer === "artifact" ? "PRODUCT ARTIFACTS" : "CODE EVIDENCE"}
            </span>
            <strong>
              {drawer === "artifact" ? "Scope plan & PRD" : "PocketPlan"}
            </strong>
          </div>
          <button onClick={close}>×</button>
        </div>
        {drawer === "artifact" ? (
          <Artifact
            analysis={analysis}
            selected={selectedOption}
            select={setSelectedOption}
            prd={prd}
            prdModel={prdModel}
            jiraSyncedAt={jiraSyncedAt}
            jiraIssueKeys={jiraIssueKeys}
            createPrd={createPrd}
            createJira={createJira}
            viewJira={viewJira}
            busy={busy}
            weeks={weeks}
          />
        ) : (
          <CodeBrowser
            tree={tree}
            file={file}
            clearFile={clearFile}
            openFile={openFile}
          />
        )}
      </aside>
    </>
  );
}

function Artifact({
  analysis,
  selected,
  select,
  prd,
  prdModel,
  jiraSyncedAt,
  jiraIssueKeys,
  createPrd,
  createJira,
  viewJira,
  busy,
  weeks,
}: {
  analysis: Analysis | null;
  selected: string | null;
  select: (value: string) => void;
  prd: string | null;
  prdModel: string | null;
  jiraSyncedAt: string | null;
  jiraIssueKeys: string[];
  createPrd: () => void;
  createJira: () => void;
  viewJira: () => void;
  busy: string;
  weeks: number | null;
}) {
  const [tab, setTab] = useState<"plan" | "prd">("plan");
  useEffect(() => {
    if (prd) setTab("prd");
  }, [prd]);
  if (!analysis)
    return (
      <div className="drawer-empty">
        <LayersIcon />
        <h2>No plan yet</h2>
        <p>
          Discuss the feature, then choose Generate plan. Claude will create the
          analysis here without taking you away from the conversation.
        </p>
      </div>
    );
  const activeOption =
    analysis.options.find((option) => option.id === selected) ||
    analysis.options[0];

  function downloadPrd() {
    if (!prd) return;
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([prd], { type: "text/markdown" }));
    const slug = (activeOption?.name || "pocketplan-feature")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    link.download = `${slug}-prd.md`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  return (
    <div className="artifact">
      <div className="artifact-tabs">
        <button
          className={tab === "plan" ? "active" : ""}
          onClick={() => setTab("plan")}
        >
          Scope plan
        </button>
        <button
          className={tab === "prd" ? "active" : ""}
          onClick={() => setTab("prd")}
        >
          Full PRD{prd && <span>✓</span>}
        </button>
      </div>
      {tab === "prd" ? (
        <div className="prd-panel">
          {prd ? (
            <>
              <div className="prd-toolbar">
                <div>
                  <strong>Product requirements document</strong>
                  <small>
                    Generated with {prdModel || "Claude"} from the approved
                    scope
                  </small>
                </div>
                <button onClick={downloadPrd}>Download .md</button>
              </div>
              <div className="prd-document markdown-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{prd}</ReactMarkdown>
              </div>
            </>
          ) : (
            <div className="prd-empty">
              <SparkIcon />
              <h2>Turn this scope into a full PRD</h2>
              <p>
                Scope will combine the selected option, discovery conversation,
                engineering plan and repository evidence into a document for
                product, design, engineering and QA.
              </p>
              <ul>
                <li>Goals, non-goals and user needs</li>
                <li>Requirements and acceptance criteria</li>
                <li>Technical impact and code evidence</li>
                <li>Metrics, risks and rollout plan</li>
              </ul>
              <button onClick={createPrd} disabled={!selected || Boolean(busy)}>
                <SparkIcon />
                {busy === "prd" ? "Writing PRD…" : "Generate full PRD"}
              </button>
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="verdict">
            <div className="verdict-labels">
              <span className={`risk ${analysis.risk}`}>
                {analysis.risk} risk
              </span>
              <span>Selected scope</span>
            </div>
            <h2>{activeOption?.name || analysis.verdict}</h2>
            <p>{activeOption?.summary || analysis.summary}</p>
            {activeOption && (
              <div className="scope-definition">
                <div>
                  <small>Included</small>
                  {activeOption.includes.slice(0, 3).map((item) => (
                    <span key={item}>＋ {item}</span>
                  ))}
                </div>
                <div>
                  <small>Not in this scope</small>
                  {activeOption.excludes.slice(0, 2).map((item) => (
                    <span key={item}>− {item}</span>
                  ))}
                </div>
              </div>
            )}
            <div className="metrics">
              <span>
                <strong>
                  {activeOption?.duration || `${analysis.feasibility}%`}
                </strong>
                {activeOption ? "Delivery window" : "Feasibility"}
              </span>
              <span>
                <strong>
                  {activeOption?.confidence ||
                    `${analysis.timeline_confidence}%`}
                </strong>
                {activeOption ? "Confidence" : "Timeline confidence"}
              </span>
              {weeks === null && analysis.estimated_weeks != null && (
                <span className="estimated-weeks-badge">
                  <strong>{analysis.estimated_weeks}w</strong>
                  Scope's estimate
                </span>
              )}
            </div>
          </div>
          <SectionTitle label="SCOPE OPTIONS" count={analysis.options.length} />
          <div className="scope-options">
            {analysis.options.map((option) => (
              <Option
                key={option.id}
                option={option}
                selected={selected === option.id}
                choose={() => select(option.id)}
              />
            ))}
          </div>
          <div className="prd-callout">
            <div>
              <SparkIcon />
              <p>
                <strong>Scope selected. Create the PRD next.</strong>
                <small>
                  The PRD will use “{activeOption?.name}” as its source of
                  truth.
                </small>
              </p>
            </div>
            <button
              onClick={() => {
                setTab("prd");
                if (!prd) void createPrd();
              }}
              disabled={!selected || Boolean(busy)}
            >
              {busy === "prd"
                ? "Writing…"
                : prd
                  ? "View PRD"
                  : "Generate full PRD"}
            </button>
          </div>
          <SectionTitle label="WORK ITEMS" count={analysis.plan.length} />
          <div className="work-items">
            {analysis.plan.map((item) => (
              <div
                key={item.temp_key}
                className={`work-item ${item.type.toLowerCase()}`}
              >
                <span>{item.type[0]}</span>
                <div>
                  <small>
                    {item.temp_key} · {item.discipline || "product"}
                  </small>
                  <strong>{item.title}</strong>
                </div>
                <b>{item.estimate || "–"}</b>
              </div>
            ))}
          </div>
          <SectionTitle label="EVIDENCE" count={analysis.evidence.length} />
          <div className="evidence-list">
            {analysis.evidence.map((item) => (
              <div key={item.id}>
                <span className={item.type}>
                  {item.type === "verified"
                    ? "✓"
                    : item.type === "inferred"
                      ? "≈"
                      : "?"}
                </span>
                <p>
                  <strong>{item.title}</strong>
                  <small title={item.path || item.detail}>
                    {item.path || item.detail}
                  </small>
                </p>
              </div>
            ))}
          </div>
          <div className={`approval-bar ${jiraSyncedAt ? "synced" : ""}`}>
            {jiraSyncedAt ? (
              <>
                <p>
                  <CheckIcon />
                  <span>
                    <strong>Already added to Jira backlog</strong>
                    {jiraIssueKeys.length
                      ? `${jiraIssueKeys.length} work items created`
                      : "This approved scope has already been synced."}
                  </span>
                </p>
                <button onClick={viewJira}>
                  <JiraIcon />
                  View Jira backlog
                </button>
              </>
            ) : (
              <>
                <p>
                  <CheckIcon />
                  <span>
                    <strong>Human approval required</strong>Nothing is written
                    to Jira until you approve.
                  </span>
                </p>
                <button
                  onClick={createJira}
                  disabled={!selected || Boolean(busy)}
                >
                  <JiraIcon />
                  {busy === "jira" ? "Creating…" : "Approve & create in Jira"}
                </button>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
function Option({
  option,
  selected,
  choose,
}: {
  option: ScopeOption;
  selected: boolean;
  choose: () => void;
}) {
  return (
    <button className={selected ? "selected" : ""} onClick={choose}>
      <span>{selected ? <CheckIcon /> : null}</span>
      <p>
        <strong>
          {option.name}
          {option.recommended && <i>Recommended</i>}
        </strong>
        <small>
          {option.duration} · {option.confidence} confidence
        </small>
      </p>
    </button>
  );
}
function SectionTitle({ label, count }: { label: string; count: number }) {
  return (
    <div className="section-title">
      <span>{label}</span>
      <b>{count}</b>
    </div>
  );
}
function CodeBrowser({
  tree,
  file,
  clearFile,
  openFile,
}: {
  tree: RepoNode[];
  file: RepoFile | null;
  clearFile: () => void;
  openFile: (path: string) => void;
}) {
  return (
    <div className="code-browser">
      {file ? (
        <>
          <button className="back-tree" onClick={clearFile}>
            ← Repository files
          </button>
          <div className="file-path">
            <CodeIcon />
            {file.path}
            <span>{file.lines} lines</span>
          </div>
          <pre>
            {file.content.split("\n").map((line, index) => (
              <div key={index}>
                <span>{index + 1}</span>
                <code>{line || " "}</code>
              </div>
            ))}
          </pre>
        </>
      ) : (
        <div className="tree">
          {tree.map((node) => (
            <Tree node={node} key={node.path} openFile={openFile} />
          ))}
        </div>
      )}
    </div>
  );
}
function Tree({
  node,
  openFile,
  depth = 0,
}: {
  node: RepoNode;
  openFile: (path: string) => void;
  depth?: number;
}) {
  const [open, setOpen] = useState(depth === 0);
  return (
    <>
      <button
        style={{ paddingLeft: `${16 + depth * 13}px` }}
        onClick={() =>
          node.type === "folder" ? setOpen(!open) : openFile(node.path)
        }
      >
        {node.type === "folder" ? <FolderIcon /> : <FileIcon />}
        <span>{node.name}</span>
      </button>
      {open &&
        node.children?.map((child) => (
          <Tree
            node={child}
            key={child.path}
            openFile={openFile}
            depth={depth + 1}
          />
        ))}
    </>
  );
}
