/**
 * GENERATED — do not edit manually.
 * Run `pnpm codegen` to regenerate from the OpenAPI schema.
 */

export interface AppConfig {
  theme: "light" | "dark";
  monitorInterval: number;
  maxConcurrentDownloads: number;
}

export interface MonitoredAccount {
  id: string;
  tiktok_username: string;
  enabled: boolean;
  last_check_at?: string;
  last_video_timestamp?: number;
  status: "ok" | "needs_review" | "paused";
  options?: Record<string, unknown>;
  avatar_url?: string;
  follower_count?: number;
  following_count?: number;
  total_likes?: number;
  video_count?: number;
  profile_last_refreshed?: string;
  backfill_status?: "idle" | "backfilling" | "paused" | "completed" | "cancelled";
  backfill_cursor?: string;
  backfill_total?: number;
  backfill_done?: number;
  capture_mode: "history_and_monitor" | "monitor_only";
}

export interface Video {
  id: string;
  monitored_account_id: string;
  tiktok_id: string;
  title: string;
  upload_date?: string;
  upload_timestamp?: number;
  file_path?: string;
  thumbnail_path?: string;
  duration?: number;
  description?: string;
  file_size?: number;
  file_hash?: string;
  metadata?: Record<string, unknown>;
  likes?: number;
  views?: number;
  downloaded_at?: string;
  status: "queued" | "downloading" | "downloaded" | "failed";
  error_text?: string;
  error_kind?: "auth" | "rate_limit" | "ip_block" | "network" | "not_found" | "unknown";
  retry_count?: number;
}

export type ActivityEvent =
  | { type: "monitor.cycle_started"; payload: { iteration: number; accounts: string[] } }
  | { type: "monitor.account_check_started"; payload: { username: string } }
  | { type: "monitor.new_videos_found"; payload: { count: number; accountId?: string } }
  | { type: "monitor.video_downloaded"; payload: { title: string; videoId: string } }
  | { type: "monitor.account_paused"; payload: { username: string; reason: string } }
  | { type: "monitor.cookie_expired"; payload: { accountId: string } }
  | { type: "monitor.cookie_expiring_soon"; payload: { accountId?: string; daysLeft: number } }
  | { type: "monitor.disk_warning"; payload: { freeGB: number; percent: number } }
  | { type: "monitor.yt_dlp_update_available"; payload: { currentVersion: string; latestVersion: string } }
  | { type: "backfill.started"; payload: { username: string; total: number } }
  | { type: "backfill.progress"; payload: { username: string; done: number; total: number } }
  | { type: "backfill.paused"; payload: { username: string; reason: string } }
  | { type: "backfill.completed"; payload: { username: string; downloaded: number } }
  | { type: "backfill.interrupted"; payload: { username: string; lastCursor: string } }
  | { type: "network.offline"; payload: { since: string } }
  | { type: "network.online"; payload: { since: string; durationHours: number; newVideosFound: number } }
  | { type: "monitor.error"; payload: { message: string; kind?: string } }
  | { type: "ping" };

export interface SystemHealth {
  status: string;
  db: string;
  disk_free_gb: number;
  yt_dlp_version: string;
  monitor: "running" | "stopped";
  network_status: "online" | "offline";
  accounts: number;
  needs_setup: boolean;
}

export interface SystemMetrics {
  accounts_ok: number;
  accounts_needs_review: number;
  accounts_paused: number;
  downloads_today: number;
  disk_free_gb: number;
  disk_total_gb: number;
  yt_dlp_version: string;
  monitor_status: string;
}

export interface AuthResponse {
  authenticated: boolean;
  needs_setup: boolean;
}
