import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Hash,
  Loader2,
  MessageSquareText,
  Play,
  Send,
  Timer,
  Users,
  XCircle,
} from "lucide-react";
import { analyzeVideos, streamChat } from "./lib/api";
import { formatDate, formatDuration } from "./lib/format";
import type { AnalysisResponse, ChatMessage, Citation, VideoLabel, VideoMetadata } from "./lib/types";

const processingSteps = [
  "Validating video URLs",
  "Fetching YouTube metadata",
  "Fetching Instagram metadata",
  "Extracting transcripts",
  "Calculating engagement",
  "Generating embeddings",
  "Building knowledge base",
  "Preparing workspace",
];

const featurePills = [
  { label: "Dynamic metadata", tone: "accent" },
  { label: "Transcript RAG", tone: "a" },
  { label: "Engagement scoring", tone: "success" },
  { label: "Source citations", tone: "warning" },
  { label: "Streaming chat", tone: "b" },
];

const suggestedQuestions = [
  "Why did A perform better?",
  "Compare the first 5 seconds",
  "What's each engagement rate?",
  "Suggest improvements for B",
  "Compare the hooks",
  "Compare clarity and pacing",
];

type FormErrors = {
  a?: string;
  b?: string;
};

type ProcessingState = "idle" | "processing" | "failed";

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export default function App() {
  const [route, setRoute] = useState(() => window.location.pathname);
  const [videoAUrl, setVideoAUrl] = useState("");
  const [videoBUrl, setVideoBUrl] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [processingState, setProcessingState] = useState<ProcessingState>("idle");
  const [activeStep, setActiveStep] = useState(0);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  useEffect(() => {
    const onPopState = () => setRoute(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    if (route === "/workspace" && !analysis) {
      navigate("/", true);
    }
  }, [analysis, route]);

  useEffect(() => {
    if (processingState !== "processing") return;
    const timer = window.setInterval(() => {
      setActiveStep((step) => Math.min(step + 1, processingSteps.length - 2));
    }, 700);
    return () => window.clearInterval(timer);
  }, [processingState]);

  const navigate = (path: string, replace = false) => {
    if (window.location.pathname === path) {
      setRoute(path);
      return;
    }
    if (replace) {
      window.history.replaceState({}, "", path);
    } else {
      window.history.pushState({}, "", path);
    }
    setRoute(path);
  };

  const validate = () => {
    const next: FormErrors = {};
    if (!/youtube\.com\/shorts\/[a-zA-Z0-9_-]+/i.test(videoAUrl.trim())) {
      next.a = "Enter a valid YouTube Short URL.";
    }
    if (!/instagram\.com\/reel(s)?\/[a-zA-Z0-9_-]+/i.test(videoBUrl.trim())) {
      next.b = "Enter a valid Instagram Reel URL.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleAnalyze = async () => {
    setGlobalError(null);
    if (!validate()) return;
    setProcessingState("processing");
    setActiveStep(0);
    setAnalysis(null);
    setMessages([]);

    try {
      const result = await analyzeVideos(videoAUrl.trim(), videoBUrl.trim());
      setAnalysis(result);
      setActiveStep(processingSteps.length);
      window.setTimeout(() => {
        setProcessingState("idle");
        navigate("/workspace");
      }, 600);
    } catch (error) {
      setProcessingState("failed");
      setGlobalError(error instanceof Error ? error.message : "Analysis service is currently unreachable. Please try again.");
    }
  };

  const sendMessage = async (text: string) => {
    if (!analysis || !text.trim()) return;
    const assistantId = crypto.randomUUID();
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: text.trim() },
      { id: assistantId, role: "assistant", content: "", citations: [], streaming: true },
    ]);

    try {
      await streamChat(
        analysis.session_id,
        text.trim(),
        (delta) => {
          setMessages((current) =>
            current.map((message) => (message.id === assistantId ? { ...message, content: message.content + delta } : message)),
          );
        },
        (citations) => {
          setMessages((current) =>
            current.map((message) => (message.id === assistantId ? { ...message, citations, streaming: false } : message)),
          );
        },
      );
      setMessages((current) => current.map((message) => (message.id === assistantId ? { ...message, streaming: false } : message)));
    } catch (error) {
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId
            ? {
                ...message,
                content: error instanceof Error ? error.message : "Analysis service unreachable. Please try again.",
                streaming: false,
              }
            : message,
        ),
      );
    }
  };

  if (route === "/workspace" && analysis) {
    return (
      <main className="app-shell workspace-shell">
        <WorkspaceTopBar sessionId={analysis.session_id} onNewComparison={() => navigate("/")} />
        <AnalysisWorkspace analysis={analysis} messages={messages} onSend={sendMessage} />
      </main>
    );
  }

  return (
    <main className="app-shell">
      <NavBar />
      <LandingPage
        videoAUrl={videoAUrl}
        videoBUrl={videoBUrl}
        setVideoAUrl={setVideoAUrl}
        setVideoBUrl={setVideoBUrl}
        errors={errors}
        processingState={processingState}
        activeStep={activeStep}
        globalError={globalError}
        onAnalyze={handleAnalyze}
      />
    </main>
  );
}

function NavBar() {
  return (
    <header className="nav-bar">
      <div className="brand-mark">
        <span aria-hidden="true">◈</span>
        <strong>CompiSMART</strong>
      </div>
      <div className="version-pill">v0.1 · Creator Intelligence</div>
    </header>
  );
}

function LandingPage(props: {
  videoAUrl: string;
  videoBUrl: string;
  setVideoAUrl: (value: string) => void;
  setVideoBUrl: (value: string) => void;
  errors: FormErrors;
  processingState: ProcessingState;
  activeStep: number;
  globalError: string | null;
  onAnalyze: () => void;
}) {
  const isProcessing = props.processingState === "processing";
  const isFailed = props.processingState === "failed";

  return (
    <section className="landing-hero">
      <div className="dot-grid" aria-hidden="true" />
      <div className="hero-content reveal-stack">
        <div className="hero-copy-panel">
          <div className="eyebrow">CREATOR PERFORMANCE ANALYSIS</div>
          <h1>
            Understand why one short-form video <span>outperformed</span> another.
          </h1>
          <p className="hero-copy">
            Drop a YouTube Short and an Instagram Reel. CompiSMART fetches metadata, extracts transcripts, calculates engagement,
            and lets you interrogate both videos with RAG-powered analysis.
          </p>
          <div className="feature-pills">
            {featurePills.map((pill) => (
              <span key={pill.label} className="feature-pill">
                <i className={`dot dot-${pill.tone}`} aria-hidden="true" />
                {pill.label}
              </span>
            ))}
          </div>
        </div>

        <section className="input-card" aria-label="Video comparison form">
          {isProcessing || isFailed ? (
            <ProcessingCard
              activeStep={props.activeStep}
              failed={isFailed}
              error={props.globalError}
              onRetry={props.onAnalyze}
            />
          ) : (
            <InputPanel
              videoAUrl={props.videoAUrl}
              videoBUrl={props.videoBUrl}
              setVideoAUrl={props.setVideoAUrl}
              setVideoBUrl={props.setVideoBUrl}
              errors={props.errors}
              onAnalyze={props.onAnalyze}
            />
          )}
        </section>
      </div>
    </section>
  );
}

function InputPanel(props: {
  videoAUrl: string;
  videoBUrl: string;
  setVideoAUrl: (value: string) => void;
  setVideoBUrl: (value: string) => void;
  errors: FormErrors;
  onAnalyze: () => void;
}) {
  return (
    <>
      <div className="input-card-header">
        <span>Enter two videos to compare</span>
      </div>
      <div className="url-stack">
        <UrlInput
          side="A"
          platform="YouTube Short"
          value={props.videoAUrl}
          onChange={props.setVideoAUrl}
          placeholder="https://youtube.com/shorts/..."
          error={props.errors.a}
        />
        <UrlInput
          side="B"
          platform="Instagram Reel"
          value={props.videoBUrl}
          onChange={props.setVideoBUrl}
          placeholder="https://instagram.com/reel/..."
          error={props.errors.b}
        />
      </div>
      <button className="analyze-button" onClick={props.onAnalyze}>
        Analyze Videos →
      </button>
    </>
  );
}

function UrlInput(props: {
  side: VideoLabel;
  platform: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  error?: string;
}) {
  const [touched, setTouched] = useState(false);
  const valid =
    props.side === "A"
      ? /youtube\.com\/shorts\/[a-zA-Z0-9_-]+/i.test(props.value.trim())
      : /instagram\.com\/reel(s)?\/[a-zA-Z0-9_-]+/i.test(props.value.trim());
  const showError = Boolean(props.error) || (touched && props.value.trim().length > 0 && !valid);

  return (
    <label className={`url-row url-row-${props.side.toLowerCase()}`}>
      <span className="url-label">
        <span className="video-chip">VIDEO {props.side}</span>
        <span className="platform-line">
          {props.side === "A" ? "▶" : "◎"} {props.platform}
        </span>
      </span>
      <span className="url-input-wrap">
        <input
          value={props.value}
          onChange={(event) => props.onChange(event.target.value)}
          onBlur={() => setTouched(true)}
          placeholder={props.placeholder}
          aria-label={`${props.platform} URL`}
          className={cx("url-input", showError && "url-input-error")}
        />
        {valid && <CheckCircle2 className="valid-icon" aria-hidden="true" />}
        {showError && <span className="input-error">{props.error ?? `Enter a valid ${props.platform} URL.`}</span>}
      </span>
    </label>
  );
}

function ProcessingCard(props: { activeStep: number; failed: boolean; error: string | null; onRetry: () => void }) {
  return (
    <div>
      <div className="processing-header">
        <span>{props.failed ? "Analysis request failed" : "Analyzing your videos..."}</span>
        {!props.failed && <Loader2 className="spin-icon" aria-hidden="true" />}
      </div>
      <p className="processing-note">Progress is estimated while the backend runs the analysis request.</p>
      <div className="processing-list">
        {processingSteps.map((step, index) => {
          const done = index < props.activeStep || props.activeStep >= processingSteps.length;
          const current = !props.failed && index === props.activeStep && props.activeStep < processingSteps.length;
          const failed = false;
          return (
            <div key={step} className={cx("processing-row", done && "done", current && "current", failed && "failed")}>
              <span className="status-icon">
                {done ? (
                  <CheckCircle2 aria-hidden="true" />
                ) : failed ? (
                  <XCircle aria-hidden="true" />
                ) : current ? (
                  <Loader2 className="spin-icon" aria-hidden="true" />
                ) : (
                  <span aria-hidden="true">○</span>
                )}
              </span>
              <span className="step-label">{step}</span>
              <span className="step-status">{done ? "✓" : failed ? "FAILED" : current ? "PROCESSING" : ""}</span>
            </div>
          );
        })}
      </div>
      {props.failed && (
        <div className="processing-error">
          <strong>Backend response</strong>
          <p>{props.error ?? "Analysis pipeline failed."}</p>
          <button onClick={props.onRetry}>Try Again</button>
        </div>
      )}
    </div>
  );
}

function WorkspaceTopBar(props: { sessionId: string; onNewComparison: () => void }) {
  return (
    <header className="workspace-topbar">
      <button className="new-comparison" onClick={props.onNewComparison}>
        <ArrowLeft aria-hidden="true" />
        New Comparison
      </button>
      <div className="workspace-pairing" aria-label="Current comparison">
        <span className="top-badge top-badge-a">▶ YouTube Short</span>
        <span className="vs">VS</span>
        <span className="top-badge top-badge-b">◎ Instagram Reel</span>
      </div>
      <div className="session-code">SESSION · {props.sessionId.slice(0, 8)}</div>
    </header>
  );
}

function AnalysisWorkspace(props: { analysis: AnalysisResponse; messages: ChatMessage[]; onSend: (text: string) => void }) {
  return (
    <section className="workspace-grid">
      <VideoCard video={props.analysis.video_a} side="A" />
      <ChatPanel sessionId={props.analysis.session_id} messages={props.messages} onSend={props.onSend} />
      <VideoCard video={props.analysis.video_b} side="B" />
    </section>
  );
}

function VideoCard({ video, side }: { video: VideoMetadata; side: VideoLabel }) {
  const [expanded, setExpanded] = useState(false);
  const unavailable = video.warnings.length > 0 || video.views == null || video.transcript.source_type === "unavailable";

  return (
    <aside className={`video-card video-card-${side.toLowerCase()}`}>
      {unavailable && (
        <div className="warning-banner">
          <AlertTriangle aria-hidden="true" />
          Some metrics unavailable from public source
        </div>
      )}
      <CardHeader video={video} side={side} />
      <EngagementHero video={video} side={side} />
      <button className="mobile-detail-toggle" onClick={() => setExpanded((value) => !value)}>
        {expanded ? "▴ Hide details" : "▾ Show details"}
      </button>
      <div className={cx("video-detail-body", expanded && "mobile-expanded")}>
        <StatGrid video={video} />
        <Divider />
        <MetaSection video={video} />
        <Divider />
        <TranscriptPreview video={video} />
      </div>
    </aside>
  );
}

function CardHeader({ video, side }: { video: VideoMetadata; side: VideoLabel }) {
  const creator = video.creator_name || video.creator_handle || "Creator unavailable";
  const handle = video.creator_handle ? `@${video.creator_handle.replace(/^@/, "")}` : "@unknown";

  return (
    <section className="card-header">
      <div className="card-header-row">
        <span className={`platform-badge ${video.platform === "youtube" ? "youtube-badge" : "instagram-badge"}`} role="img" aria-label={video.platform}>
          {video.platform === "youtube" ? "▶ YOUTUBE SHORT" : "◎ INSTAGRAM REEL"}
        </span>
        <span className={`video-label video-label-${side.toLowerCase()}`}>VIDEO {side}</span>
      </div>
      <h2>{creator}</h2>
      <p>
        {handle}
        <Users aria-hidden="true" />
        {compactNumber(video.follower_count)} followers
      </p>
      {video.title_or_caption && <div className="caption-preview">{video.title_or_caption}</div>}
    </section>
  );
}

function EngagementHero({ video, side }: { video: VideoMetadata; side: VideoLabel }) {
  const rate = video.engagement_rate;
  return (
    <section className={`engagement-hero engagement-${side.toLowerCase()}`}>
      <div className="metric-label">ENGAGEMENT RATE</div>
      <div className={`engagement-number ${engagementTone(rate)}`}>{rate == null ? "—" : `${rate.toFixed(2)}%`}</div>
      <div className="hairline" />
      <p>{rate == null ? "Views data unavailable" : rate > 5 ? "High signal for this audience" : rate >= 2 ? "Moderate competitive signal" : "Needs stronger retention signals"}</p>
    </section>
  );
}

function StatGrid({ video }: { video: VideoMetadata }) {
  return (
    <dl className="stat-grid">
      <StatCell label="Views" value={compactNumber(video.views)} />
      <StatCell label="Likes" value={compactNumber(video.likes)} />
      <StatCell label="Comments" value={compactNumber(video.comments)} />
    </dl>
  );
}

function StatCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-cell">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function MetaSection({ video }: { video: VideoMetadata }) {
  const [showAllTags, setShowAllTags] = useState(false);
  const visibleTags = showAllTags ? video.hashtags : video.hashtags.slice(0, 2);
  const extra = Math.max(video.hashtags.length - 2, 0);

  return (
    <section className="meta-section">
      <MetaRow icon={<CalendarDays />} label="Upload Date" value={formatDate(video.upload_date).replace("Unavailable", "—")} />
      <MetaRow icon={<Timer />} label="Duration" value={formatDuration(video.duration_seconds).replace("Unavailable", "—")} />
      <div className="meta-row">
        <Hash aria-hidden="true" />
        <span className="meta-key">Hashtags</span>
        <span className="meta-value hashtag-list">
          {visibleTags.length > 0 ? visibleTags.map((tag) => <span key={tag}>{tag}</span>) : "—"}
          {!showAllTags && extra > 0 && (
            <button onClick={() => setShowAllTags(true)} type="button">
              +{extra} more
            </button>
          )}
        </span>
      </div>
      <div className="meta-row">
        <MessageSquareText aria-hidden="true" />
        <span className="meta-key">Transcript</span>
        <span className="meta-value">
          {video.transcript.source_type === "unavailable" ? "Unavailable" : "Available"}{" "}
          <TranscriptBadge source={video.transcript.source_type} />
        </span>
      </div>
    </section>
  );
}

function MetaRow({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="meta-row">
      <span className="meta-icon">{icon}</span>
      <span className="meta-key">{label}</span>
      <span className="meta-value">{value}</span>
    </div>
  );
}

function TranscriptBadge({ source }: { source: VideoMetadata["transcript"]["source_type"] }) {
  return <span className={`transcript-badge transcript-${source}`}>{source.replace("_", " ")}</span>;
}

function TranscriptPreview({ video }: { video: VideoMetadata }) {
  const [expanded, setExpanded] = useState(false);
  const text = video.transcript.text?.trim();

  return (
    <section className="transcript-preview">
      <div className="metric-label">TRANSCRIPT PREVIEW</div>
      <div className="hairline" />
      {!text ? (
        <p>Transcript unavailable. Analysis uses metadata only.</p>
      ) : (
        <>
          <p className={expanded ? "transcript-full" : "line-clamp-3"}>“{text}”</p>
          <button onClick={() => setExpanded((value) => !value)}>{expanded ? "Collapse transcript ↑" : "Show full transcript ↓"}</button>
        </>
      )}
    </section>
  );
}

function ChatPanel(props: { sessionId: string; messages: ChatMessage[]; onSend: (text: string) => void }) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const isStreaming = useMemo(() => props.messages.some((message) => message.streaming), [props.messages]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [props.messages]);

  const submit = (value = draft) => {
    if (!value.trim() || isStreaming) return;
    props.onSend(value);
    setDraft("");
  };

  return (
    <section className="chat-panel">
      <header className="chat-header">
        <div className="chat-title">
          <span aria-hidden="true">◈</span>
          <strong>Analysis Chat</strong>
        </div>
        <div className="chat-context">
          <span className="mini-dot mini-a" />
          A ↔ B · {props.messages.length} messages
          <span className="mini-dot mini-b" />
        </div>
      </header>
      <div ref={scrollRef} className="messages-area" aria-live="polite">
        {props.messages.length === 0 ? <SuggestedQuestions onSelect={submit} disabled={isStreaming} /> : props.messages.map((message) => <ChatBubble key={message.id} message={message} />)}
      </div>
      <ChatInputBar
        draft={draft}
        setDraft={setDraft}
        isStreaming={isStreaming}
        sessionId={props.sessionId}
        onSubmit={submit}
      />
    </section>
  );
}

function SuggestedQuestions({ onSelect, disabled }: { onSelect: (value: string) => void; disabled: boolean }) {
  return (
    <div className="suggested-questions">
      <div className="suggested-glyph" aria-hidden="true">◈</div>
      <p>Ask anything about these videos</p>
      <div className="question-grid">
        {suggestedQuestions.map((question) => (
          <button key={question} onClick={() => onSelect(question)} disabled={disabled}>
            <ArrowRight aria-hidden="true" />
            {question}
          </button>
        ))}
      </div>
    </div>
  );
}

function ChatInputBar(props: {
  draft: string;
  setDraft: (value: string) => void;
  isStreaming: boolean;
  sessionId: string;
  onSubmit: () => void;
}) {
  return (
    <form
      className="chat-input-bar"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <div className="input-line">
        <textarea
          value={props.draft}
          onChange={(event) => props.setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              props.onSubmit();
            }
          }}
          placeholder="✦ Ask about these videos..."
          rows={1}
          aria-label="Ask about these videos"
        />
        <button disabled={!props.draft.trim() || props.isStreaming} aria-label="Send message">
          <ArrowUp aria-hidden="true" />
        </button>
      </div>
      <p>Powered by Cohere · RAG from ChromaDB · Session {props.sessionId.slice(0, 8)}</p>
    </form>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <article className="message-row user-row">
        <div>
          <div className="message-label">YOU</div>
          <div className="user-bubble">{message.content}</div>
          <time>{new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>
        </div>
      </article>
    );
  }

  return (
    <article className="message-row assistant-row">
      <div className="assistant-avatar" aria-hidden="true">◈</div>
      <div className="assistant-message">
        <div className="assistant-bubble">
          {message.content ? <MarkdownLite content={message.content} /> : <StreamingIndicator />}
          {message.streaming && message.content && <span className="stream-cursor" aria-hidden="true" />}
        </div>
        {message.citations && message.citations.length > 0 && <CitationChips citations={message.citations} />}
      </div>
    </article>
  );
}

function MarkdownLite({ content }: { content: string }) {
  return (
    <div className="markdown-lite">
      {content.split("\n").map((line, index) => (
        <p key={`${line}-${index}`}>{line || "\u00A0"}</p>
      ))}
    </div>
  );
}

function StreamingIndicator() {
  return (
    <span className="streaming-dots" aria-label="Assistant is typing">
      <i />
      <i />
      <i />
    </span>
  );
}

function CitationChips({ citations }: { citations: Citation[] }) {
  return (
    <div className="citation-row">
      {citations.map((citation) => (
        <span key={`${citation.video_label}-${citation.chunk_id}`} className={`citation-chip citation-${citation.video_label.toLowerCase()}`}>
          <span aria-hidden="true">#</span>
          {citation.video_label}-{citation.chunk_id} · {citation.platform === "youtube" ? "Video A" : "Video B"} · Chunk
          <span className="tooltip">{citation.text_preview.slice(0, 80)}</span>
        </span>
      ))}
    </div>
  );
}

function Divider() {
  return <div className="divider" />;
}

function compactNumber(value?: number | null): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en", {
    notation: value >= 10000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(value);
}

function engagementTone(value?: number | null): string {
  if (value == null) return "tone-muted";
  if (value > 5) return "tone-success";
  if (value >= 2) return "tone-warning";
  return "tone-error";
}
