# CompiSMART — Frontend Redesign Specification
### Engineering Design Document for Codex Implementation

---

## 0. Design Philosophy

**Aesthetic Direction:** Dark analytical intelligence. Think mission control meets editorial data journalism.

The UI should feel like a tool that a serious creator strategist would actually pay for — not a demo project, not a ChatGPT wrapper, not a "vibe-coded" hackathon submission.

Reference visual vocabulary: Perplexity's chat density + Linear's spatial precision + Vercel's terminal-elegance + Bloomberg Terminal's data confidence.

**The one thing users remember:** A cinematic split-screen workspace where two videos "compete" in side-by-side dossiers, and the AI chat lives between them like a referee making the call.

**No generic AI aesthetics. No purple gradients. No bouncing spinners. No confetti.**

---

## 1. Tech Stack Constraints

- React + Vite + TypeScript
- TailwindCSS (utility classes only — no arbitrary values unless specified)
- TanStack Query for server state
- `framer-motion` for animations
- `lucide-react` for icons
- `react-markdown` + `remark-gfm` for rendering chat responses
- `clsx` / `tailwind-merge` for conditional classes

---

## 2. Design Tokens

Define all tokens as CSS custom properties in `index.css` or `globals.css`. Do not hardcode hex values in components.

```css
:root {
  /* Backgrounds */
  --bg-base:       #080A0D;
  --bg-surface:    #0F1318;
  --bg-elevated:   #141920;
  --bg-overlay:    #1A2028;

  /* Borders */
  --border-subtle: #1E2530;
  --border-default:#252E3A;
  --border-strong: #2E3A48;

  /* Text */
  --text-primary:  #EDF2F7;
  --text-secondary:#8A95A3;
  --text-muted:    #4A5568;
  --text-ghost:    #2D3748;

  /* Accent — Electric Blue */
  --accent:        #3B82F6;
  --accent-dim:    rgba(59, 130, 246, 0.12);
  --accent-glow:   rgba(59, 130, 246, 0.25);

  /* Video A — Indigo (YouTube) */
  --video-a:       #6366F1;
  --video-a-dim:   rgba(99, 102, 241, 0.10);
  --video-a-border:rgba(99, 102, 241, 0.30);

  /* Video B — Rose (Instagram) */
  --video-b:       #F43F5E;
  --video-b-dim:   rgba(244, 63, 94, 0.10);
  --video-b-border:rgba(244, 63, 94, 0.30);

  /* Status */
  --success:       #10B981;
  --warning:       #F59E0B;
  --error:         #EF4444;

  /* Misc */
  --radius-sm:     6px;
  --radius-md:     10px;
  --radius-lg:     16px;
  --radius-xl:     22px;

  /* Shadows */
  --shadow-card:   0 1px 3px rgba(0,0,0,0.4), 0 4px 16px rgba(0,0,0,0.3);
  --shadow-glow-a: 0 0 24px rgba(99, 102, 241, 0.15);
  --shadow-glow-b: 0 0 24px rgba(244, 63, 94, 0.15);
}
```

---

## 3. Typography

Use Google Fonts. Load in `index.html`:

```html
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap" rel="stylesheet">
```

| Role | Font | Weight | Size | Line Height |
|---|---|---|---|---|
| Brand / Hero title | Syne | 800 | 48px / clamp(32px, 6vw, 56px) | 1.05 |
| Section headers | Syne | 700 | 22px | 1.2 |
| Card labels | Syne | 600 | 13px | 1.3 |
| Body copy | DM Sans | 400 | 15px | 1.65 |
| Body emphasis | DM Sans | 500 | 15px | 1.65 |
| Metadata / chips | DM Sans | 400 | 12px | 1.4 |
| Code / Chunk IDs | IBM Plex Mono | 400 | 11px | 1.5 |
| Engagement rate (big) | IBM Plex Mono | 500 | 28px | 1 |
| Stats numbers | IBM Plex Mono | 400 | 15px | 1 |

Apply via Tailwind font utilities + custom font-family config in `tailwind.config.ts`:

```ts
fontFamily: {
  display: ['Syne', 'sans-serif'],
  body: ['DM Sans', 'sans-serif'],
  mono: ['IBM Plex Mono', 'monospace'],
}
```

---

## 4. Page Architecture (Routes)

```
/             → LandingPage
/workspace    → AnalysisWorkspace  (only accessible after /analyze completes)
```

Use React Router v6. Redirect from `/workspace` to `/` if no session data exists in context.

---

## 5. Landing Page

### 5.1 Overall Structure

```
┌─────────────────────────────────────────────────────┐
│  NavBar                                              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Hero Section (centered, ~100vh)                    │
│    Eyebrow text                                      │
│    H1 headline                                       │
│    Subheadline                                       │
│    FeaturePills row                                  │
│                                                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  InputPanel (the main action card)                  │
│    VideoURLInput × 2                                 │
│    AnalyzeButton                                     │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 5.2 NavBar

```
[ ◈ CompiSMART ]                    [ v0.1 · Creator Intelligence ]
```

- Height: 56px. `position: sticky; top: 0; z-index: 50`.
- Background: `--bg-base` with `backdrop-filter: blur(12px)`.
- Bottom border: 1px solid `--border-subtle`.
- Logo: `◈` glyph in `--accent` color + "CompiSMART" in Syne 700. No linking needed.
- Right side: small pill badge with text "v0.1 · Creator Intelligence" in `--text-muted`, `--bg-elevated`, `--border-subtle` border, `border-radius: var(--radius-sm)`, font-size 11px.

### 5.3 Hero Section

Full viewport height (`min-h-[calc(100vh-56px)]`), flex column, centered.

**Background treatment:**
- Base: `--bg-base`
- Layered radial gradient: one soft indigo bloom top-left (`rgba(99,102,241,0.06)`) and one soft rose bloom bottom-right (`rgba(244,63,94,0.05)`)
- Fine dot grid pattern (CSS only): use `background-image: radial-gradient(circle, var(--border-subtle) 1px, transparent 1px)` with `background-size: 24px 24px`. Opacity 0.4.

**Content (centered column, max-width 680px):**

1. **Eyebrow** — small all-caps chip above the headline:
   - Text: `CREATOR PERFORMANCE ANALYSIS`
   - Style: `font-family: IBM Plex Mono`, 10px, letter-spacing 0.15em, color `--accent`, background `--accent-dim`, border `1px solid var(--accent-glow)`, border-radius `var(--radius-sm)`, padding `4px 10px`

2. **H1 Headline:**
   ```
   Understand why one short-form
   video outperformed another.
   ```
   - Font: Syne 800, `clamp(32px, 5vw, 52px)`, color `--text-primary`
   - Line-height: 1.08
   - Word "outperformed" → wrapped in a `<span>` with `--video-a` color (indigo). Creates natural visual accent without design clichés.

3. **Subheadline:**
   ```
   Drop a YouTube Short and an Instagram Reel. CompiSMART
   fetches metadata, extracts transcripts, calculates engagement,
   and lets you interrogate both videos with RAG-powered analysis.
   ```
   - Font: DM Sans 400, 16px, color `--text-secondary`, max-width 560px, centered.

4. **Feature Pills row** (horizontal, flex, wrap, centered, gap 8px):

   Each pill has:
   - Background: `--bg-elevated`
   - Border: `1px solid var(--border-default)`
   - Border-radius: `var(--radius-sm)`
   - Padding: `5px 12px`
   - Font: DM Sans 500, 12px, `--text-secondary`
   - A tiny colored dot (`●`) prefix in varying colors per pill

   Pills:
   | Dot Color | Label |
   |---|---|
   | `--accent` | Dynamic metadata |
   | `--video-a` | Transcript RAG |
   | `--success` | Engagement scoring |
   | `--warning` | Source citations |
   | `--video-b` | Streaming chat |

### 5.4 Input Panel

A single card, centered, max-width 600px. Appears below the hero copy with `margin-top: 48px`.

**Card style:**
- Background: `--bg-surface`
- Border: `1px solid var(--border-default)`
- Border-radius: `var(--radius-xl)`
- Padding: 32px
- Box-shadow: `var(--shadow-card)`

**Inside the card:**

1. **Card header:**
   - Text: "Enter two videos to compare" in DM Sans 500, 13px, `--text-muted`
   - Small horizontal rule below it: `1px solid var(--border-subtle)`

2. **Two URL inputs stacked** with 16px gap between them.

   Each input row has:
   - A left-side label column (fixed 80px):
     - Label chip: pill-shaped div with background `--video-a-dim` (or `--video-b-dim` for second), border matching, text `VIDEO A` / `VIDEO B` in IBM Plex Mono 500, 10px, letter-spacing 0.1em, color `--video-a` / `--video-b`.
     - Below the chip: platform icon + platform name in `--text-muted`, 11px. (YouTube icon SVG inline + "YouTube Short" for A; Instagram icon SVG inline + "Instagram Reel" for B)
   - A right-side input field (flex-grow):
     - Background: `--bg-elevated`
     - Border: `1px solid var(--border-default)`
     - Border-radius: `var(--radius-md)`
     - Padding: `12px 16px`
     - Font: DM Sans 400, 14px, `--text-primary`
     - Placeholder: `https://youtube.com/shorts/...` / `https://instagram.com/reel/...`
     - Placeholder color: `--text-ghost`
     - On focus: border changes to `--video-a` / `--video-b` with a matching `box-shadow: 0 0 0 3px var(--video-a-dim)` / `var(--video-b-dim)`
     - On valid URL entered: show a small green checkmark icon (Lucide `CheckCircle2`, 14px, `--success`) at right end of input (use `position: relative` with `position: absolute` icon)
     - On invalid URL: red border + inline error message in DM Sans 400, 12px, `--error`, appearing below the input with a fade-in animation

3. **Analyze Button:**
   - Full width
   - Height: 52px
   - Background: `--accent`
   - Border-radius: `var(--radius-md)`
   - Font: Syne 700, 15px, white
   - Text: `Analyze Videos →`
   - On hover: brightness increases slightly (`filter: brightness(1.08)`), subtle upward shift (`transform: translateY(-1px)`), `box-shadow: 0 4px 20px var(--accent-glow)`
   - On click/active: `transform: translateY(0)`
   - Disabled state (during processing): background `--bg-elevated`, color `--text-muted`, cursor `not-allowed`, no hover effects
   - Loading state: replace text with a row of three animated dots (CSS keyframe, sequential opacity pulse, 400ms stagger)

### 5.5 Landing Page Animations

Use `framer-motion`. Stagger children in a `motion.div` container with `staggerChildren: 0.08`.

- Eyebrow chip: fade + 8px rise, delay 0
- H1: fade + 12px rise, delay 0.08s
- Subheadline: fade + 8px rise, delay 0.16s
- Feature pills: fade + 6px rise, delay 0.24s
- Input card: fade + 16px rise, delay 0.32s

Duration for each: 0.5s, ease `[0.22, 1, 0.36, 1]` (custom spring approximation).

---

## 6. Processing / Loading Overlay

After "Analyze Videos" is clicked, the input card transforms into a **processing card** in-place (no route change yet).

### 6.1 Processing Card

Replace the input card contents with a step tracker. Keep the same card shell.

**Header:**
```
Analyzing your videos...
[spinning thin arc loader, 20px, --accent color]
```

**Step list:**

```
● Validating video URLs          [DONE / IN PROGRESS / PENDING]
● Fetching YouTube metadata      [...]
● Fetching Instagram metadata    [...]
● Extracting transcripts         [...]
● Calculating engagement         [...]
● Generating embeddings          [...]
● Building knowledge base        [...]
● Preparing workspace            [...]
```

Each step row:
- Height: 40px, border-bottom `1px solid var(--border-subtle)` except last
- Left: status icon (16px)
  - Pending: `○` in `--text-ghost`
  - In progress: Lucide `Loader2` (16px) with spin animation, `--accent`
  - Done: Lucide `CheckCircle2` (16px), `--success`
  - Failed: Lucide `XCircle` (16px), `--error`
- Step label: DM Sans 400, 14px
  - Pending: `--text-muted`
  - In progress: `--text-primary`
  - Done: `--text-secondary` + `text-decoration: line-through` (subtle strikethrough)
  - Failed: `--error`
- Right: status badge text (IBM Plex Mono, 11px):
  - Pending: hidden
  - In progress: `PROCESSING` in `--accent`
  - Done: timestamp or `✓` in `--success`
  - Failed: `FAILED` in `--error`

**When all steps complete:** Run a 600ms delay then `navigate('/workspace')`.

**If any step fails:** Show error inline on that step row. Show a "Try Again" link below the step list.

---

## 7. Analysis Workspace (`/workspace`)

### 7.1 Layout

Three-panel layout. Full viewport height. No scrolling at the outer level (panels scroll internally).

```
┌──────────────────────────────────────────────────────────────────────┐
│  WorkspaceTopBar                                                      │
├──────────────┬───────────────────────────┬───────────────────────────┤
│              │                           │                           │
│  VideoCard   │    ChatPanel              │   VideoCard               │
│  (Video A)   │                           │   (Video B)               │
│              │                           │                           │
│  28%         │    44%                    │   28%                     │
└──────────────┴───────────────────────────┴───────────────────────────┘
```

Outer container: `display: grid; grid-template-columns: 28fr 44fr 28fr; height: calc(100vh - 56px)`. All three panels: `overflow-y: auto`.

Panel gaps: none (borders between panels instead). Left panel: `border-right: 1px solid var(--border-subtle)`. Right panel: `border-left: 1px solid var(--border-subtle)`.

### 7.2 WorkspaceTopBar

Height: 48px. Background `--bg-surface`. Border-bottom `1px solid var(--border-subtle)`.

Left section:
- `←` arrow icon (Lucide `ArrowLeft`, 16px) + "New Comparison" text. Clicking navigates back to `/`.

Center section (absolute centered):
- Two small platform badges side by side, separated by `VS` text
  - `[ ▶ YouTube Short ]` — indigo background `--video-a-dim`, indigo border, `--video-a` text
  - `VS` in IBM Plex Mono, `--text-muted`, mx-3
  - `[ ◎ Instagram Reel ]` — rose background `--video-b-dim`, rose border, `--video-b` text
  - Each badge: 10px Syne 600, all-caps, padding `4px 10px`, border-radius `var(--radius-sm)`

Right section:
- Session ID shown in IBM Plex Mono 400, 11px, `--text-ghost`: `SESSION · {session_id_truncated}`

---

## 8. Video Card Component

This is the left and right panel content. Same component for both — accepts a `video` prop and a `side: 'A' | 'B'` prop.

### 8.1 Card Architecture

```
VideoCard
  ├── CardHeader          (platform + label + creator)
  ├── EngagementHero      (big engagement rate number)
  ├── StatGrid            (views, likes, comments)
  ├── Divider
  ├── MetaSection         (upload date, duration, hashtags)
  ├── Divider
  └── TranscriptPreview   (first 200 chars of transcript)
```

### 8.2 CardHeader

Padding: 20px 20px 0.

```
[ PLATFORM BADGE ]                              [ VIDEO A ]
Creator Name
@handle · 4.2M followers
```

- **Platform badge:**
  - YouTube: background `rgba(255,0,0,0.12)`, border `1px solid rgba(255,0,0,0.25)`, text `▶ YOUTUBE SHORT` in IBM Plex Mono 10px, `#FF4444`
  - Instagram: gradient border technique — use `background-clip: padding-box` + pseudo-element for the gradient border. Text `◎ INSTAGRAM REEL` in IBM Plex Mono 10px, `--video-b`.

- **Video label** (top-right): `VIDEO A` / `VIDEO B` in Syne 600, 11px. Color: `--video-a` / `--video-b`. Background: `--video-a-dim` / `--video-b-dim`. Padding `3px 8px`. Border-radius `var(--radius-sm)`.

- **Creator name:** Syne 700, 18px, `--text-primary`.
- **Handle + follower count:** DM Sans 400, 13px, `--text-secondary`. Lucide `Users` icon (12px) before follower count.

### 8.3 EngagementHero

Padding: 16px 20px.

Background: for Video A, a very subtle top-to-bottom gradient from `--video-a-dim` to transparent. For Video B, `--video-b-dim` to transparent.

```
ENGAGEMENT RATE
6.42%
──────────────────────
"Top 12% for this niche"   [optional if available]
```

- Label: IBM Plex Mono 500, 10px, `--text-muted`, letter-spacing 0.12em, all-caps.
- Number: IBM Plex Mono 500, 36px. Color: if engagement > 5% → `--success`; if 2-5% → `--warning`; if <2% → `--error`. Otherwise `--text-primary`.
- Thin horizontal rule: `1px solid var(--border-subtle)` below the number.

### 8.4 StatGrid

A 3-column grid inside the card. Each stat cell:

```
┌────────┬────────┬────────┐
│  VIEWS │  LIKES │COMMENTS│
│ 1.2M   │  84K   │  3.2K  │
└────────┴────────┴────────┘
```

- Grid: `display: grid; grid-template-columns: repeat(3, 1fr)`. 1px border dividers between cells.
- Each cell padding: 14px 12px.
- Label: IBM Plex Mono 400, 9px, `--text-muted`, all-caps, letter-spacing 0.1em.
- Number: IBM Plex Mono 500, 18px, `--text-primary`.
- Format numbers: use `Intl.NumberFormat` — `1200000` → `1.2M`, `84000` → `84K`, etc.
- Unavailable data: show `—` in `--text-ghost`.

### 8.5 MetaSection

Padding: 14px 20px.

Compact key-value rows:

```
📅  Upload Date     Jan 14, 2025
⏱  Duration         0:31
🏷  Hashtags         #shorts  #marketing  +3 more
📝  Transcript       Available  [whisper_generated badge]
```

- Icon: Lucide icons, 13px, `--text-muted`
- Key: DM Sans 500, 12px, `--text-muted`
- Value: DM Sans 400, 12px, `--text-secondary`
- Row height: 28px
- Hashtags: show first 2, then `+N more` in a clickable chip (no modal needed, just expand inline on click)
- Transcript source badge: inline pill
  - `official_caption` → green
  - `whisper_generated` → amber
  - `scraped_caption` → blue
  - `unavailable` → red
  - Style: IBM Plex Mono, 9px, all-caps, matching color background (10% opacity), matching colored border, padding `2px 6px`.

### 8.6 TranscriptPreview

Padding: 14px 20px 20px.

```
TRANSCRIPT PREVIEW
─────────────────────────
"So the reason most creators fail in the first..."
[Show full transcript ↓]
```

- Section label: IBM Plex Mono 400, 9px, `--text-muted`, letter-spacing 0.12em, all-caps.
- Preview text: DM Sans 400, 13px, `--text-secondary`, `font-style: italic`, max 3 lines with `line-clamp: 3`.
- "Show full transcript" toggle: DM Sans 500, 12px, `--accent`. On click, expands to full scrollable transcript in a `<pre>`-like block with IBM Plex Mono 11px.

### 8.7 Unavailable States

If metadata is partially unavailable, show a non-intrusive banner at the top of the card:

```
[ ⚠ Some metrics unavailable from public source ]
```

- Background: `rgba(245, 158, 11, 0.08)`
- Border: `1px solid rgba(245, 158, 11, 0.20)`
- Border-radius: `var(--radius-sm)`
- Text: DM Sans 400, 12px, `--warning`
- Icon: Lucide `AlertTriangle`, 12px

---

## 9. Chat Panel

### 9.1 Chat Panel Structure

```
ChatPanel
  ├── ChatPanelHeader          (title + context indicators)
  ├── MessagesArea             (scrollable, flex-col)
  │     ├── SuggestedQuestions (only shown when empty)
  │     ├── UserMessage
  │     ├── AssistantMessage
  │     │     └── CitationsList
  │     └── StreamingMessage   (typing state)
  └── ChatInputBar             (sticky bottom)
```

### 9.2 ChatPanelHeader

Height: 52px. Background: `--bg-surface`. Border-bottom: `1px solid var(--border-subtle)`.

```
[ ◈ Analysis Chat ]         [ A ↔ B · 3 messages ]
```

- Left: `◈` icon in `--accent` (16px) + "Analysis Chat" in Syne 700, 14px, `--text-primary`.
- Right: small status indicator showing `A ↔ B` with `--video-a` and `--video-b` colored dots + message count in IBM Plex Mono 11px, `--text-muted`.

### 9.3 MessagesArea

Background: `--bg-base`. Flex column, padding 20px. Gap between messages: 20px. `overflow-y: auto`.

Scrolls to bottom automatically on new message. Use `useEffect` + `ref.scrollIntoView`.

### 9.4 Suggested Questions

Only visible when there are 0 messages. Appears in center of MessagesArea.

```
    ◈
  Ask anything about these videos

  [ Why did A perform better?     ]
  [ Compare the first 5 seconds   ]
  [ What's each engagement rate?  ]
  [ Suggest improvements for B    ]
  [ Compare the hooks             ]
  [ Compare clarity and pacing    ]
```

- Icon: `◈` in `--accent`, 24px, centered.
- Title: DM Sans 400, 14px, `--text-muted`, centered.
- Question chips: rendered as a 2-column grid, each chip:
  - Background: `--bg-elevated`
  - Border: `1px solid var(--border-default)`
  - Border-radius: `var(--radius-md)`
  - Padding: `12px 16px`
  - Font: DM Sans 400, 13px, `--text-secondary`
  - Left icon: Lucide `ArrowRight`, 12px, `--text-ghost`
  - On hover: border → `--border-strong`, text → `--text-primary`, `transform: translateX(2px)`
  - Clicking a chip populates and submits the input

### 9.5 UserMessage

```
                              [message text] [YOU]
```

Right-aligned. Max-width: 75%.

- Bubble background: `--accent` with slight transparency (`rgba(59, 130, 246, 0.15)`)
- Border: `1px solid rgba(59, 130, 246, 0.25)`
- Border-radius: `var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg)` (all corners rounded except bottom-right = user "tail")
- Padding: `12px 16px`
- Font: DM Sans 400, 14px, `--text-primary`
- Label "YOU": IBM Plex Mono 400, 10px, `--text-muted`, to the right above the bubble.
- Timestamp: IBM Plex Mono 400, 10px, `--text-ghost`, below bubble.

### 9.6 AssistantMessage

```
[◈]  [message text...]
     [citation chips]
```

Left-aligned. Max-width: 90%.

- Avatar circle (28px): `--bg-elevated`, border `1px solid var(--border-default)`, contains `◈` in `--accent`, 12px.
- Bubble background: `--bg-surface`
- Border: `1px solid var(--border-default)`
- Border-radius: `var(--radius-sm) var(--radius-lg) var(--radius-lg) var(--radius-lg)`
- Padding: `16px`
- Font: DM Sans 400, 14px, `--text-secondary` (base), with `--text-primary` for emphasis.
- Markdown rendering: `react-markdown` + `remark-gfm`. Style:
  - `strong` → DM Sans 600, `--text-primary`
  - `h3` / `h4` → Syne 600, `--text-primary`, smaller size
  - `code` inline → IBM Plex Mono 12px, `--bg-elevated`, padding `2px 6px`, border-radius 4px
  - `ul/ol` → normal list rendering with `--text-secondary`
  - `blockquote` → left border `3px solid var(--accent-glow)`, background `--accent-dim`, padding 8px 12px, `--text-secondary`

### 9.7 Streaming Indicator

While the assistant is generating a response, show a streaming message bubble in place:

- Same style as AssistantMessage bubble.
- Inside: a blinking cursor — three dots `•••` with sequential CSS opacity animation (IBM Plex Mono, `--accent`).
- Text streams in word-by-word. Use a `useState` that appends each token as it arrives from the SSE stream.

### 9.8 Citation Chips

Appear below each completed AssistantMessage. A horizontal flex-wrap row.

Each citation is a small chip:

```
[ A-001  Video A · Chunk ]     [ B · Metadata ]
```

- Background:
  - Video A citations: `--video-a-dim`
  - Video B citations: `--video-b-dim`
  - Metadata citations: `--bg-elevated`
- Border: matching dim border (0.30 opacity)
- Border-radius: `var(--radius-sm)`
- Padding: `4px 10px`
- Font: IBM Plex Mono 400, 10px
- Color: `--video-a` / `--video-b` / `--text-muted`
- Left: small `#` symbol in `--text-ghost`
- On hover: show a small tooltip with the transcript text preview (first 80 chars). Tooltip background `--bg-overlay`, border `1px solid var(--border-default)`, DM Sans 400, 12px.

### 9.9 ChatInputBar

Sticky to bottom of chat panel. Background: `--bg-surface`. Border-top: `1px solid var(--border-subtle)`. Padding: 12px 16px 16px.

```
┌─────────────────────────────────────────────────────┐
│  [ ✦ Ask about these videos...          ] [ Send → ] │
└─────────────────────────────────────────────────────┘
```

- Textarea (not input): auto-grows from 1 line to max 4 lines. Background `--bg-elevated`. Border `1px solid var(--border-default)`. Border-radius `var(--radius-md)`. Padding `12px 16px`. Font DM Sans 400, 14px. Placeholder `--text-ghost`.
- On focus: border → `--accent`, box-shadow `0 0 0 3px var(--accent-dim)`.
- Submit button (send icon): `--accent` background, 40px × 40px, `border-radius: var(--radius-md)`, `ml-3`. Lucide `ArrowUp` icon (18px), white.
  - Disabled when textarea is empty or when streaming.
- Keyboard: `Enter` submits (without shift). `Shift+Enter` adds newline.
- Below the input, in very small text: IBM Plex Mono 400, 10px, `--text-ghost`. Centered: `Powered by Cohere · RAG from ChromaDB · Session {short_id}`

---

## 10. Mobile Layout

Breakpoint: below `768px`.

```
┌────────────────────────────┐
│  NavBar (56px)             │
├────────────────────────────┤
│  Video A Card              │
├────────────────────────────┤
│  Video B Card              │
├────────────────────────────┤
│  Chat Messages Area        │
│  (flex-grow, overflow-y)   │
├────────────────────────────┤
│  ChatInputBar (sticky)     │
└────────────────────────────┘
```

- Three-column grid becomes single column with `flex-direction: column`.
- Video cards are collapsed by default on mobile: show only header + engagement rate. A `▾ Show details` toggle expands the rest.
- Chat panel takes remaining viewport height: `flex: 1; min-height: 50vh`.
- ChatInputBar: `position: sticky; bottom: 0`.

---

## 11. Component File Structure

```
src/
  components/
    layout/
      NavBar.tsx
      WorkspaceTopBar.tsx
    landing/
      HeroSection.tsx
      FeaturePills.tsx
      InputPanel.tsx          ← URLInput + AnalyzeButton
      URLInput.tsx
      ProcessingCard.tsx
    workspace/
      VideoCard.tsx
        CardHeader.tsx
        EngagementHero.tsx
        StatGrid.tsx
        MetaSection.tsx
        TranscriptPreview.tsx
      ChatPanel.tsx
        SuggestedQuestions.tsx
        MessagesArea.tsx
        UserMessage.tsx
        AssistantMessage.tsx
        CitationChips.tsx
        ChatInputBar.tsx
        StreamingIndicator.tsx
    shared/
      Badge.tsx               ← reusable pill/badge
      Divider.tsx
      Tooltip.tsx
  pages/
    LandingPage.tsx
    AnalysisWorkspace.tsx
  hooks/
    useAnalysis.ts            ← TanStack mutation for /analyze
    useStreamingChat.ts       ← SSE hook for /chat
    useVideoFormat.ts         ← number formatting helpers
  context/
    SessionContext.tsx        ← stores session_id + video metadata
  styles/
    globals.css               ← CSS custom properties (tokens)
  lib/
    api.ts                    ← typed API clients
    validators.ts             ← URL validation regexes
```

---

## 12. API Integration Notes

### URL Validation Patterns

```ts
// YouTube Shorts
/youtube\.com\/shorts\/[a-zA-Z0-9_-]+/

// Instagram Reels
/instagram\.com\/reel(s)?\/[a-zA-Z0-9_-]+/
```

Validate on blur and on submit. Show inline errors.

### SSE Streaming

`/chat` returns Server-Sent Events. Handle with `EventSource` or a custom `ReadableStream` fetch.

```ts
// useStreamingChat.ts pattern
const response = await fetch('/chat', { method: 'POST', body: JSON.stringify(...) });
const reader = response.body!.getReader();
// Decode chunks and append to message state token by token
```

Emit a `[DONE]` sentinel to mark stream end. Then parse citations from the final message metadata.

### Session Context

After `/analyze` responds successfully, store in context:

```ts
interface SessionData {
  sessionId: string;
  videoA: VideoMetadata;
  videoB: VideoMetadata;
}
```

This allows `WorkspaceTopBar`, `VideoCard`s, and `ChatPanel` to all pull from a single source of truth.

---

## 13. Micro-Interaction Inventory

| Element | Trigger | Effect |
|---|---|---|
| URL Input | Valid URL entered | Green checkmark fades in right side |
| URL Input | Invalid URL | Red border + error text drops in (0.2s ease) |
| Analyze Button | Hover | `translateY(-1px)`, glow shadow |
| Processing Steps | Step completes | Checkmark scales in (spring), row dims |
| Video Card | Initial mount | Slides in from side (A from left, B from right), 0.4s delay after workspace loads |
| Suggested question chip | Hover | `translateX(2px)`, border brightens |
| User message send | Submit | Chip slides up into chat from input bar |
| Citation chip | Hover | Tooltip fades in upward |
| Streaming text | Token append | Text appears character by character (no jump) |
| Chat scroll | New message | Smooth scroll to bottom (behavior: smooth) |

---

## 14. Error + Empty States Summary

| State | Location | Display |
|---|---|---|
| Empty workspace (no session) | `/workspace` | Redirect to `/` |
| Instagram scrape failed | Video B card header | Amber warning banner |
| Transcript unavailable | TranscriptPreview | "Transcript unavailable. Analysis uses metadata only." |
| Engagement rate unavailable | EngagementHero | `—` in `--text-ghost` with tooltip "Views data unavailable" |
| Chat error | MessagesArea | Error bubble: "Analysis service unreachable. Please try again." styled as assistant message with `--error` border |
| Analysis pipeline failure | ProcessingCard | Failed step highlighted, "Try Again" button |

---

## 15. Accessibility Notes

- All interactive elements: `focus-visible` ring using `var(--accent)` outline, 2px offset.
- Color is never the sole differentiator: all status states have both color AND icon/text.
- Textarea and inputs: proper `aria-label` or associated `<label>`.
- Streaming message region: `aria-live="polite"` on the messages container.
- Lucide icons used decoratively: `aria-hidden="true"`.
- Video card platform badges: `role="img" aria-label="YouTube Short"`.

---

## 16. Implementation Order for Codex

Build in this sequence to unblock UI testing at each step:

1. `globals.css` with all CSS tokens
2. `tailwind.config.ts` with font families
3. `NavBar.tsx` (static)
4. `LandingPage.tsx` shell + `HeroSection.tsx` (static content, no logic)
5. `InputPanel.tsx` + `URLInput.tsx` (with validation logic)
6. `SessionContext.tsx`
7. `api.ts` (typed fetch wrappers for `/health`, `/analyze`, `/chat`)
8. `useAnalysis.ts` (TanStack mutation)
9. `ProcessingCard.tsx` (step animation)
10. Route `/workspace` → `AnalysisWorkspace.tsx` shell
11. `WorkspaceTopBar.tsx`
12. `VideoCard.tsx` + all sub-components
13. `ChatPanel.tsx` shell + static layout
14. `SuggestedQuestions.tsx`
15. `UserMessage.tsx` + `AssistantMessage.tsx` + `CitationChips.tsx`
16. `useStreamingChat.ts` + live SSE integration
17. `StreamingIndicator.tsx`
18. Mobile responsive pass
19. `framer-motion` animation pass (add after logic is working)
20. Final polish: accessibility, error states, empty states
