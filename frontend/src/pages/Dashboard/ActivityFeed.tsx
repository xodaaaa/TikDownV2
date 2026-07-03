import { useEffect, useRef, useState } from "react";
import { useEventSource } from "@/hooks/useEventSource";
import { useEvents } from "@/services/queries";
import Badge from "@/components/Badge";
import { formatTime } from "@/utils/date";
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Download,
  UserMinus,
  Clock,
  HardDrive,
  Globe,
  Eye,
  type LucideIcon,
} from "lucide-react";

const SSE_URL = import.meta.env.VITE_SSE_URL ?? "/api/events";

interface ApiEvent {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

const eventConfig: Record<
  string,
  { icon: LucideIcon; variant: "success" | "warning" | "danger" | "default"; label: string }
> = {
  "monitor.cycle_started": { icon: RefreshCw, variant: "default", label: "Cycle" },
  "monitor.account_check_started": { icon: Eye, variant: "default", label: "Checking" },
  "monitor.new_videos_found": { icon: Download, variant: "success", label: "New videos" },
  "monitor.video_downloaded": { icon: Download, variant: "success", label: "Downloaded" },
  "monitor.account_paused": { icon: UserMinus, variant: "warning", label: "Paused" },
  "monitor.cookie_expired": { icon: AlertTriangle, variant: "danger", label: "Cookie expired" },
  "monitor.cookie_expiring_soon": { icon: Clock, variant: "warning", label: "Cookie expiring" },
  "monitor.disk_warning": { icon: HardDrive, variant: "danger", label: "Disk warning" },
  "monitor.yt_dlp_update_available": { icon: Download, variant: "warning", label: "yt-dlp update" },
  "monitor.error": { icon: XCircle, variant: "danger", label: "Error" },
  "network.offline": { icon: Globe, variant: "danger", label: "Offline" },
  "network.online": { icon: Globe, variant: "success", label: "Online" },
  "backfill.started": { icon: Download, variant: "warning", label: "Backfill started" },
  "backfill.progress": { icon: RefreshCw, variant: "warning", label: "Backfill progress" },
  "backfill.paused": { icon: UserMinus, variant: "warning", label: "Backfill paused" },
  "backfill.completed": { icon: CheckCircle, variant: "success", label: "Backfill done" },
  "backfill.interrupted": { icon: XCircle, variant: "danger", label: "Backfill interrupted" },
};

function getSuggestion(type: string, payload?: Record<string, unknown>): string | null {
  if (type === "monitor.error" || type === "monitor.cookie_expired") {
    const kind = payload?.kind as string | undefined;
    if (kind === "auth") return "Re-importa las cookies desde el navegador";
    if (kind === "rate_limit") return "Sube el intervalo mínimo";
    if (kind === "ip_block") return "Verifica la reputación de tu IP de salida";
    return "Sube una cookie nueva en Settings";
  }
  if (type === "monitor.cookie_expiring_soon") {
    return `Quedan ${String(payload?.daysLeft ?? "")} días. Re-importa pronto.`;
  }
  if (type === "monitor.disk_warning") return "Libera espacio en el volumen";
  return null;
}

export default function ActivityFeed() {
  const { data: history } = useEvents(50);
  const [liveEvents, setLiveEvents] = useState<ApiEvent[]>([]);
  const [autoscroll, setAutoscroll] = useState(true);
  const feedRef = useRef<HTMLDivElement>(null);

  const { connected } = useEventSource(SSE_URL, {
    onMessage: (data: unknown) => {
      const ev = data as { type?: string; payload?: Record<string, unknown> } | null;
      if (ev?.type && ev.type !== "ping") {
        setLiveEvents((prev) => [
          { id: crypto.randomUUID(), type: ev.type!, payload: ev.payload ?? {}, created_at: new Date().toISOString() },
          ...prev,
        ].slice(0, 100));
      }
    },
  });

  const allEvents: ApiEvent[] = [
    ...liveEvents,
    ...((history ?? []) as ApiEvent[]),
  ].slice(0, 100);

  useEffect(() => {
    if (autoscroll && feedRef.current) {
      feedRef.current.scrollTop = 0;
    }
  }, [allEvents, autoscroll]);

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-200">Activity Feed</span>
          <span
            className={`inline-flex h-2 w-2 rounded-full ${connected ? "bg-emerald-400" : "bg-red-400"}`}
          />
        </div>
        <label className="flex items-center gap-1.5 text-xs text-gray-500">
          <input
            type="checkbox"
            checked={autoscroll}
            onChange={(e) => setAutoscroll(e.target.checked)}
            className="rounded border-gray-700 bg-gray-800 text-accent-500"
          />
          Autoscroll
        </label>
      </div>

      <div ref={feedRef} className="flex max-h-80 flex-col gap-1 overflow-y-auto font-mono text-xs">
        {allEvents.length === 0 && (
          <p className="py-8 text-center text-gray-600">No hay eventos todavía</p>
        )}
        {allEvents.map((ev) => {
          const cfg = eventConfig[ev.type] ?? {
            icon: Eye,
            variant: "default" as const,
            label: ev.type,
          };
          const Icon = cfg.icon;
          const suggestion = getSuggestion(ev.type, ev.payload);
          const p = ev.payload ?? {};

          return (
            <div key={ev.id} className="border-b border-gray-800/50 py-1.5 last:border-0">
              <div className="flex items-start gap-2">
                <span className="shrink-0 text-gray-600">
                  {ev.created_at ? formatTime(ev.created_at) : ""}
                </span>
                <Badge variant={cfg.variant} className="shrink-0">
                  <Icon className="mr-1 h-3 w-3" />
                  {cfg.label}
                </Badge>
                <span className="text-gray-400">
                  {String(p.message ?? p.username ?? p.title ?? "")}
                  {p.count != null && ` (${String(p.count)})`}
                  {p.done != null && p.total != null && ` ${String(p.done)}/${String(p.total)}`}
                </span>
              </div>
              {suggestion && (
                <p className="mt-0.5 pl-[4.5rem] text-gray-600">↳ {suggestion}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
