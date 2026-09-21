import { useEffect, useRef, useState } from "react";
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
  SparkIcon,
} from "./icons";
import type {
  Analysis,
  Bootstrap,
  ChatMessage,
  JiraIssue,
  LlmStatus,
  RepoFile,
  RepoNode,
  ScopeOption,
} from "./types";

const starterMessage: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi Weifa — I’m connected to the ExpenseFlow codebase. Tell me what you want to build and the delivery window. I’ll ask only the questions that materially change the plan.",
  createdAt: "Now",
};

type Drawer = "artifact" | "code" | "jira" | null;
type BusyState = "chat" | "plan" | "jira" | "";

function newId(): string {
  if (
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
  ) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function App() {
  const [data, setData] = useState<Bootstrap | null>(null);
  const [status, setStatus] = useState<LlmStatus | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    starterMessage,
  ]);
  const [input, setInput] = useState("");
  const [weeks, setWeeks] = useState(4);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [selectedOption, setSelectedOption] = useState<
    string | null
  >(null);
  const [jira, setJira] = useState<JiraIssue[]>([]);
  const [tree, setTree] = useState<RepoNode[]>([]);
  const [file, setFile] = useState<RepoFile | null>(null);
  const [busy, setBusy] = useState<BusyState>("");
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] =
    useState(false);
  const [drawer, setDrawer] = useState<Drawer>(null);

  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      try {
        const [bootstrap, repoTree, llmStatus] =
          await Promise.all([
            api.bootstrap(),
            api.tree(),
            api.llmStatus(),
          ]);

        if (cancelled) {
          return;
        }

        setData(bootstrap);
        setJira(bootstrap.jira);
        setTree(repoTree);
        setStatus(llmStatus);
      } catch (err) {
        if (cancelled) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load Scope",
        );
      }
    }

    void loadInitialData();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, busy]);

  const userMessageCount = messages.filter(
    (message) => message.role === "user",
  ).length;

  async function send(
    mode: "chat" | "plan",
    suggested?: string,
  ) {
    if (busy) {
      return;
    }

    const text = (suggested ?? input).trim();
    let nextMessages = messages;

    if (text) {
      const userMessage: ChatMessage = {
        id: newId(),
        role: "user",
        content: text,
        createdAt: "Now",
      };

      nextMessages = [...messages, userMessage];

      setMessages(nextMessages);
      setInput("");
    }

    const hasUserMessage = nextMessages.some(
      (message) => message.role === "user",
    );

    if (!hasUserMessage) {
      return;
    }

    setBusy(mode);
    setError("");

    try {
      const result = await api.chat(
        nextMessages,
        mode,
        weeks,
      );

      const assistantMessage: ChatMessage = {
        id: newId(),
        role: "assistant",
        content: result.message,
        createdAt: "Now",
      };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);

      if (result.analysis) {
        const recommendedOption =
          result.analysis.options.find(
            (option) => option.recommended,
          ) ?? result.analysis.options[0];

        setAnalysis(result.analysis);
        setSelectedOption(
          recommendedOption?.id ?? null,
        );
        setDrawer("artifact");
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Claude request failed",
      );
    } finally {
      setBusy("");
    }
  }

  async function createJira() {
    if (!analysis || !selectedOption || busy) {
      return;
    }

    setBusy("jira");
    setError("");

    try {
      await api.approve(
        analysis.feature_id,
        selectedOption,
      );

      const created = await api.syncJira(
        analysis.feature_id,
      );

      const updatedIssues = await api.jira();

      setJira(updatedIssues);

      setMessages((current) => [
        ...current,
        {
          id: newId(),
          role: "assistant",
          content: `Done — ${created.length} approved work items were created in the mock ExpenseFlow Jira project.`,
          createdAt: "Now",
        },
      ]);

      setDrawer("jira");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Jira sync failed",
      );
    } finally {
      setBusy("");
    }
  }

  async function openFile(path: string) {
    setError("");

    try {
      const selectedFile = await api.file(path);

      setFile(selectedFile);
      setDrawer("code");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to open the selected file",
      );
    }
  }

  function newChat() {
    setMessages([starterMessage]);
    setAnalysis(null);
    setSelectedOption(null);
    setInput("");
    setError("");
    setDrawer(null);
    setSidebarOpen(false);
  }

  if (!data || !status) {
    return (
      <div className="loading">
        <div className="logo">S/</div>
        <span>
          {error || "Connecting product context…"}
        </span>
      </div>
    );
  }

  return (
    <div
      className={`app ${
        sidebarCollapsed ? "collapsed" : ""
      }`}
    >
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
        open={sidebarOpen}
        collapsed={sidebarCollapsed}
        close={() => setSidebarOpen(false)}
        toggle={() =>
          setSidebarCollapsed((current) => !current)
        }
        newChat={newChat}
        openRepo={() => {
          setFile(null);
          setDrawer("code");
          setSidebarOpen(false);
        }}
        openJira={() => {
          setDrawer("jira");
          setSidebarOpen(false);
        }}
      />

      <main className="workspace">
        <Header
          data={data}
          status={status}
          openMenu={() => setSidebarOpen(true)}
          openArtifact={() => setDrawer("artifact")}
        />

        {!status.configured && <ConfigBanner />}

        {error && (
          <div className="error-banner">
            <span>!</span>
            <p>{error}</p>
            <button
              type="button"
              aria-label="Dismiss error"
              onClick={() => setError("")}
            >
              ×
            </button>
          </div>
        )}

        <section className="conversation">
          <div className="chat-width">
            <div className="conversation-head">
              <span className="kicker">
                FEATURE PLANNING SESSION
              </span>

              <h1>
                What should ExpenseFlow do next?
              </h1>

              <p>
                Talk it through naturally. Scope keeps the
                product and code context in the conversation.
              </p>
            </div>

            <div className="messages">
              {messages.map((message, index) => (
                <Message
                  key={message.id}
                  message={message}
                  model={status.model}
                  last={
                    index === messages.length - 1
                  }
                />
              ))}

              {busy && <Thinking mode={busy} />}

              <div ref={endRef} />
            </div>

            {userMessageCount === 0 && (
              <div className="prompts">
                <Prompt
                  n="01"
                  title="Edit after submission"
                  text="Assess a workflow-changing request"
                  onClick={() =>
                    void send(
                      "chat",
                      "Allow employees to edit a submitted expense for 24 hours. We need it within four weeks.",
                    )
                  }
                />

                <Prompt
                  n="02"
                  title="Receipt OCR"
                  text="Explore an AI-assisted feature"
                  onClick={() =>
                    void send(
                      "chat",
                      "Add receipt OCR that extracts merchant, date, currency and amount, with a correction flow.",
                    )
                  }
                />

                <Prompt
                  n="03"
                  title="Multiple currencies"
                  text="Surface hidden finance dependencies"
                  onClick={() =>
                    void send(
                      "chat",
                      "Support expenses in multiple currencies and reimburse employees in SGD.",
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
          send={() => void send("chat")}
          generate={() => void send("plan")}
          disabled={
            !status.configured || Boolean(busy)
          }
          canGenerate={userMessageCount > 0}
        />
      </main>

      <ContextDrawer
        drawer={drawer}
        close={() => setDrawer(null)}
        analysis={analysis}
        selectedOption={selectedOption}
        setSelectedOption={setSelectedOption}
        createJira={() => void createJira()}
        busy={busy}
        tree={tree}
        file={file}
        clearFile={() => setFile(null)}
        openFile={(path) => void openFile(path)}
        jira={jira}
      />
    </div>
  );
}

type SidebarProps = {
  data: Bootstrap;
  status: LlmStatus;
  open: boolean;
  collapsed: boolean;
  close: () => void;
  toggle: () => void;
  newChat: () => void;
  openRepo: () => void;
  openJira: () => void;
};

function Sidebar({
  data,
  status,
  open,
  collapsed,
  close,
  toggle,
  newChat,
  openRepo,
  openJira,
}: SidebarProps) {
  return (
    <aside
      className={[
        "sidebar",
        open ? "mobile-open" : "",
        collapsed ? "is-collapsed" : "",
      ].join(" ")}
    >
      <div className="brand">
        <div className="logo">S/</div>

        <div className="brand-copy">
          <strong>scope</strong>
          <span>product intelligence</span>
        </div>

        <button
          type="button"
          className="close-mobile"
          aria-label="Close menu"
          onClick={close}
        >
          ×
        </button>
      </div>

      <button
        type="button"
        className="new-chat"
        onClick={newChat}
      >
        <span>＋</span>
        <b>New feature</b>
      </button>

      <div className="side-section">
        <label>RECENT</label>

        <button
          type="button"
          className="recent active"
        >
          <FileIcon />

          <span>
            <strong>New feature plan</strong>
            <small>Just now</small>
          </span>
        </button>

        <button type="button" className="recent">
          <FileIcon />

          <span>
            <strong>Receipt OCR</strong>
            <small>Yesterday</small>
          </span>
        </button>
      </div>

      <div className="side-section connections">
        <label>CONNECTIONS</label>

        <button type="button" onClick={openRepo}>
          <GitIcon />

          <span>
            <strong>{data.repository.name}</strong>
            <small>
              <i /> {data.repository.files} files indexed
            </small>
          </span>
        </button>

        <button type="button" onClick={openJira}>
          <JiraIcon />

          <span>
            <strong>ExpenseFlow Jira</strong>
            <small>
              <i /> Mock project connected
            </small>
          </span>
        </button>

        <button type="button">
          <SparkIcon />

          <span>
            <strong>Claude</strong>
            <small>
              <i
                className={
                  status.configured ? "" : "off"
                }
              />

              {status.configured
                ? status.model
                : "Setup required"}
            </small>
          </span>
        </button>
      </div>

      <div className="side-footer">
        <div className="avatar">W</div>

        <span>
          <strong>Weifa</strong>
          <small>Product manager</small>
        </span>

        <button
          type="button"
          className="collapse-button"
          onClick={toggle}
          title={
            collapsed
              ? "Expand sidebar"
              : "Collapse sidebar"
          }
        >
          {collapsed ? "›" : "‹"}
        </button>
      </div>
    </aside>
  );
}

type HeaderProps = {
  data: Bootstrap;
  status: LlmStatus;
  openMenu: () => void;
  openArtifact: () => void;
};

function Header({
  data,
  status,
  openMenu,
  openArtifact,
}: HeaderProps) {
  return (
    <header className="header">
      <button
        type="button"
        className="menu-button"
        aria-label="Open menu"
        onClick={openMenu}
      >
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
          <strong>Code context ready</strong>
          <small>
            {data.repository.commit} · indexed
          </small>
        </p>
      </div>

      <div className="header-right">
        <span
          className={`model-status ${
            status.configured ? "" : "offline"
          }`}
        >
          <SparkIcon />

          {status.configured
            ? status.model
            : "Claude offline"}
        </span>

        <button
          type="button"
          className="mobile-plan"
          onClick={openArtifact}
        >
          <LayersIcon />
          <span>Plan</span>
        </button>

        <div className="team">
          {data.team.slice(0, 3).map((member) => (
            <i key={member.name}>
              {member.initials}
            </i>
          ))}
        </div>
      </div>
    </header>
  );
}

type MessageProps = {
  message: ChatMessage;
  model: string;
  last: boolean;
};

function Message({
  message,
  model,
  last,
}: MessageProps) {
  if (message.role === "user") {
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
  }

  return (
    <article
      className={`message assistant-message ${
        last ? "latest" : ""
      }`}
    >
      <div className="ai-avatar">
        <SparkIcon />
      </div>

      <div>
        <div className="message-meta">
          <strong>Scope</strong>
          <span>{model}</span>
        </div>

        <div className="message-body">
          {message.content
            .split("\n")
            .filter(Boolean)
            .map((part, index) => (
              <p key={`${message.id}-${index}`}>
                {part}
              </p>
            ))}
        </div>
      </div>
    </article>
  );
}

function Thinking({ mode }: { mode: BusyState }) {
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
              : mode === "jira"
                ? "Creating the approved Jira work…"
                : "Reading the product context…"}
          </span>
        </div>
      </div>
    </article>
  );
}

type PromptProps = {
  n: string;
  title: string;
  text: string;
  onClick: () => void;
};

function Prompt({
  n,
  title,
  text,
  onClick,
}: PromptProps) {
  return (
    <button type="button" onClick={onClick}>
      <span>{n}</span>

      <p>
        <strong>{title}</strong>
        {text}
      </p>

      <ArrowIcon />
    </button>
  );
}

type ComposerProps = {
  input: string;
  setInput: (value: string) => void;
  weeks: number;
  setWeeks: (value: number) => void;
  send: () => void;
  generate: () => void;
  disabled: boolean;
  canGenerate: boolean;
};

function Composer({
  input,
  setInput,
  weeks,
  setWeeks,
  send,
  generate,
  disabled,
  canGenerate,
}: ComposerProps) {
  return (
    <div className="composer-wrap">
      <div className="composer">
        <textarea
          rows={1}
          placeholder="Describe the feature, answer a question, or change the scope…"
          value={input}
          disabled={disabled}
          onChange={(event) =>
            setInput(event.target.value)
          }
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              !event.shiftKey
            ) {
              event.preventDefault();
              send();
            }
          }}
        />

        <div className="composer-tools">
          <div className="timeline">
            <span>Target</span>

            <button
              type="button"
              aria-label="Reduce target duration"
              disabled={disabled}
              onClick={() =>
                setWeeks(Math.max(1, weeks - 1))
              }
            >
              −
            </button>

            <strong>{weeks} weeks</strong>

            <button
              type="button"
              aria-label="Increase target duration"
              disabled={disabled}
              onClick={() =>
                setWeeks(Math.min(52, weeks + 1))
              }
            >
              ＋
            </button>
          </div>

          <div className="composer-actions">
            <button
              type="button"
              className="generate"
              onClick={generate}
              disabled={disabled || !canGenerate}
            >
              <SparkIcon />
              Generate plan
            </button>

            <button
              type="button"
              className="send"
              onClick={send}
              disabled={
                disabled || !input.trim()
              }
              aria-label="Send message"
            >
              <ArrowIcon />
            </button>
          </div>
        </div>
      </div>

      <small>
        Claude can make mistakes. Engineering should
        verify code evidence before Jira creation.
      </small>
    </div>
  );
}

function ConfigBanner() {
  return (
    <div className="config-banner">
      <span>Claude is not configured</span>

      <p>
        Add{" "}
        <code>
          ANTHROPIC_AUTH_TOKEN
        </code>{" "}
        and{" "}
        <code>ANTHROPIC_BASE_URL</code> to{" "}
        <code>backend/.env</code>, then restart FastAPI.
      </p>
    </div>
  );
}

type ContextDrawerProps = {
  drawer: Drawer;
  close: () => void;
  analysis: Analysis | null;
  selectedOption: string | null;
  setSelectedOption: (value: string) => void;
  createJira: () => void;
  busy: BusyState;
  tree: RepoNode[];
  file: RepoFile | null;
  clearFile: () => void;
  openFile: (path: string) => void;
  jira: JiraIssue[];
};

function ContextDrawer({
  drawer,
  close,
  analysis,
  selectedOption,
  setSelectedOption,
  createJira,
  busy,
  tree,
  file,
  clearFile,
  openFile,
  jira,
}: ContextDrawerProps) {
  if (!drawer) {
    return null;
  }

  const heading =
    drawer === "artifact"
      ? "GENERATED PLAN"
      : drawer === "code"
        ? "CODE EVIDENCE"
        : "JIRA PREVIEW";

  const title =
    drawer === "artifact"
      ? "Engineering brief"
      : drawer === "code"
        ? "ExpenseFlow"
        : "ExpenseFlow board";

  return (
    <>
      <button
        type="button"
        className="drawer-scrim"
        aria-label="Close drawer"
        onClick={close}
      />

      <aside className="context-drawer">
        <div className="drawer-head">
          <div>
            <span>{heading}</span>
            <strong>{title}</strong>
          </div>

          <button
            type="button"
            aria-label="Close drawer"
            onClick={close}
          >
            ×
          </button>
        </div>

        {drawer === "artifact" && (
          <Artifact
            analysis={analysis}
            selected={selectedOption}
            select={setSelectedOption}
            createJira={createJira}
            busy={busy}
          />
        )}

        {drawer === "code" && (
          <CodeBrowser
            tree={tree}
            file={file}
            clearFile={clearFile}
            openFile={openFile}
          />
        )}

        {drawer === "jira" && (
          <JiraPreview issues={jira} />
        )}
      </aside>
    </>
  );
}

type ArtifactProps = {
  analysis: Analysis | null;
  selected: string | null;
  select: (value: string) => void;
  createJira: () => void;
  busy: BusyState;
};

function Artifact({
  analysis,
  selected,
  select,
  createJira,
  busy,
}: ArtifactProps) {
  if (!analysis) {
    return (
      <div className="drawer-empty">
        <LayersIcon />

        <h2>No plan yet</h2>

        <p>
          Discuss the feature, then choose Generate plan.
          Claude will create the analysis here without
          taking you away from the conversation.
        </p>
      </div>
    );
  }

  return (
    <div className="artifact">
      <div className="verdict">
        <span className={`risk ${analysis.risk}`}>
          {analysis.risk} risk
        </span>

        <h2>{analysis.verdict}</h2>

        <p>{analysis.summary}</p>

        <div className="metrics">
          <span>
            <strong>
              {analysis.feasibility}%
            </strong>
            Feasibility
          </span>

          <span>
            <strong>
              {analysis.timeline_confidence}%
            </strong>
            Timeline confidence
          </span>
        </div>
      </div>

      <SectionTitle
        label="SCOPE OPTIONS"
        count={analysis.options.length}
      />

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

      <SectionTitle
        label="WORK ITEMS"
        count={analysis.plan.length}
      />

      <div className="work-items">
        {analysis.plan.map((item) => (
          <div
            key={item.temp_key}
            className={`work-item ${item.type.toLowerCase()}`}
          >
            <span>{item.type[0]}</span>

            <div>
              <small>
                {item.temp_key} ·{" "}
                {item.discipline || "product"}
              </small>

              <strong>{item.title}</strong>
            </div>

            <b>{item.estimate ?? "–"}</b>
          </div>
        ))}
      </div>

      <SectionTitle
        label="EVIDENCE"
        count={analysis.evidence.length}
      />

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

              <small>
                {item.path || item.detail}
              </small>
            </p>
          </div>
        ))}
      </div>

      <div className="approval-bar">
        <p>
          <CheckIcon />

          <span>
            <strong>
              Human approval required
            </strong>
            Nothing is written to Jira until you
            approve.
          </span>
        </p>

        <button
          type="button"
          onClick={createJira}
          disabled={
            !selected || Boolean(busy)
          }
        >
          <JiraIcon />

          {busy === "jira"
            ? "Creating…"
            : "Approve & create in Jira"}
        </button>
      </div>
    </div>
  );
}

type OptionProps = {
  option: ScopeOption;
  selected: boolean;
  choose: () => void;
};

function Option({
  option,
  selected,
  choose,
}: OptionProps) {
  return (
    <button
      type="button"
      className={selected ? "selected" : ""}
      onClick={choose}
    >
      <span>
        {selected ? <CheckIcon /> : null}
      </span>

      <p>
        <strong>
          {option.name}

          {option.recommended && (
            <i>Recommended</i>
          )}
        </strong>

        <small>
          {option.duration} · {option.confidence}{" "}
          confidence
        </small>
      </p>
    </button>
  );
}

function SectionTitle({
  label,
  count,
}: {
  label: string;
  count: number;
}) {
  return (
    <div className="section-title">
      <span>{label}</span>
      <b>{count}</b>
    </div>
  );
}

type CodeBrowserProps = {
  tree: RepoNode[];
  file: RepoFile | null;
  clearFile: () => void;
  openFile: (path: string) => void;
};

function CodeBrowser({
  tree,
  file,
  clearFile,
  openFile,
}: CodeBrowserProps) {
  if (!file) {
    return (
      <div className="code-browser">
        <div className="tree">
          {tree.map((node) => (
            <Tree
              node={node}
              key={node.path}
              openFile={openFile}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="code-browser">
      <button
        type="button"
        className="back-tree"
        onClick={clearFile}
      >
        ← Repository files
      </button>

      <div className="file-path">
        <CodeIcon />
        {file.path}
        <span>{file.lines} lines</span>
      </div>

      <pre>
        {file.content.split("\n").map((line, index) => (
          <div key={`${file.path}-${index}`}>
            <span>{index + 1}</span>
            <code>{line || " "}</code>
          </div>
        ))}
      </pre>
    </div>
  );
}

type TreeProps = {
  node: RepoNode;
  openFile: (path: string) => void;
  depth?: number;
};

function Tree({
  node,
  openFile,
  depth = 0,
}: TreeProps) {
  const [open, setOpen] = useState(depth === 0);

  return (
    <>
      <button
        type="button"
        style={{
          paddingLeft: `${16 + depth * 13}px`,
        }}
        onClick={() => {
          if (node.type === "folder") {
            setOpen((current) => !current);
          } else {
            openFile(node.path);
          }
        }}
      >
        {node.type === "folder" ? (
          <FolderIcon />
        ) : (
          <FileIcon />
        )}

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

function JiraPreview({
  issues,
}: {
  issues: JiraIssue[];
}) {
  const generatedIssues = issues.filter((issue) =>
    issue.labels.includes("scope-generated"),
  );

  return (
    <div className="jira-preview">
      <div className="jira-summary">
        <JiraIcon />

        <p>
          <strong>
            {generatedIssues.length
              ? `${generatedIssues.length} generated issues`
              : "Mock Jira is ready"}
          </strong>

          <small>
            {generatedIssues.length
              ? "Created from the approved Scope plan"
              : "Approve a generated plan to create linked work"}
          </small>
        </p>
      </div>

      {issues.map((issue) => (
        <article key={issue.key}>
          <span
            className={issue.type.toLowerCase()}
          >
            {issue.type[0]}
          </span>

          <div>
            <small>
              {issue.key} · {issue.status}
            </small>

            <strong>{issue.summary}</strong>
            <p>{issue.description}</p>
          </div>

          <b>{issue.estimate ?? "–"}</b>
        </article>
      ))}
    </div>
  );
}