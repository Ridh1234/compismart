import type { AnalysisProgress, AnalysisResponse, Citation } from "./types";

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export function mediaProxyUrl(url: string): string {
  return `${API_BASE}/media/proxy?url=${encodeURIComponent(url)}`;
}

export async function analyzeVideos(videoAUrl: string, videoBUrl: string): Promise<AnalysisResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ video_a_url: videoAUrl, video_b_url: videoBUrl }),
    });
  } catch (error) {
    throw new Error(`Could not reach backend at ${API_BASE || "same-origin"}. Confirm the API server is running.`);
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail?.message ?? payload?.message ?? `Analysis service returned HTTP ${response.status}.`);
  }
  return response.json();
}

export async function streamAnalyzeVideos(
  videoAUrl: string,
  videoBUrl: string,
  onProgress: (progress: AnalysisProgress) => void,
): Promise<AnalysisResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/analyze/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ video_a_url: videoAUrl, video_b_url: videoBUrl }),
    });
  } catch (error) {
    throw new Error(`Could not reach backend at ${API_BASE || "same-origin"}. Confirm the API server is running.`);
  }

  if (!response.ok || !response.body) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail?.message ?? payload?.message ?? `Analysis service returned HTTP ${response.status}.`);
  }

  let result: AnalysisResponse | null = null;
  await readSseStream(response, (event, data) => {
    if (event === "progress" || event === "heartbeat") onProgress(data as AnalysisProgress);
    if (event === "result") result = data as AnalysisResponse;
    if (event === "error") throw new Error(data.message ?? "Analysis failed.");
  });

  if (!result) {
    throw new Error("Analysis stream ended before returning a result.");
  }
  return result;
}

export async function streamChat(
  sessionId: string,
  message: string,
  onDelta: (text: string) => void,
  onCitations: (citations: Citation[]) => void,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
  } catch (error) {
    throw new Error(`Could not reach backend at ${API_BASE || "same-origin"}. Confirm the API server is running.`);
  }
  if (!response.ok || !response.body) {
    throw new Error("Analysis service is currently unreachable. Please try again.");
  }

  await readSseStream(response, (event, data) => {
    if (event === "delta") onDelta(data.text ?? "");
    if (event === "citations") onCitations(data.citations ?? []);
    if (event === "error") throw new Error(data.message ?? "Chat failed.");
  });
}

async function readSseStream(response: Response, onEvent: (event: string, data: any) => void): Promise<void> {
  if (!response.body) {
    throw new Error("Streaming response body was empty.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const rawEvent of events) {
      const lines = rawEvent.split("\n");
      const event = lines.find((line) => line.startsWith("event:"))?.replace("event:", "").trim();
      const dataLine = lines.find((line) => line.startsWith("data:"))?.replace("data:", "").trim();
      if (!event || !dataLine) continue;
      const data = JSON.parse(dataLine);
      onEvent(event, data);
    }
  }
}
