export type Platform = "youtube" | "instagram";
export type VideoLabel = "A" | "B";

export type TranscriptBundle = {
  text: string;
  source_type: "official_caption" | "scraped_caption" | "whisper_generated" | "unavailable";
  warning?: string | null;
};

export type VideoMetadata = {
  label: VideoLabel;
  platform: Platform;
  source_url: string;
  video_id?: string | null;
  creator_name?: string | null;
  creator_handle?: string | null;
  follower_count?: number | null;
  title_or_caption?: string | null;
  views?: number | null;
  likes?: number | null;
  comments?: number | null;
  hashtags: string[];
  upload_date?: string | null;
  duration_seconds?: number | null;
  engagement_rate?: number | null;
  thumbnail_url?: string | null;
  transcript: TranscriptBundle;
  warnings: string[];
};

export type AnalysisResponse = {
  session_id: string;
  video_a: VideoMetadata;
  video_b: VideoMetadata;
  warnings: string[];
};

export type Citation = {
  video_label: VideoLabel;
  chunk_id: string;
  platform: Platform;
  text_preview: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  streaming?: boolean;
};
