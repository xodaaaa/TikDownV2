import { useState, useRef, useEffect } from "react";
import { useLogs } from "@/services/queries";
import Badge from "@/components/Badge";
import Skeleton from "@/components/Skeleton";

const LEVELS = ["", "INFO", "WARNING", "ERROR"] as const;

const levelBadge: Record<string, "success" | "warning" | "danger" | "default"> = {
  INFO: "success",
  WARNING: "warning",
  ERROR: "danger",
};

export default function LogsViewer() {
  const [level, setLevel] = useState<string>("");
  const { data: logs, isLoading } = useLogs(level || undefined);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-8 w-40 rounded-lg" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-500">Nivel:</span>
        <div className="flex gap-1">
          {LEVELS.map((l) => (
            <button
              key={l}
              onClick={() => setLevel(l)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                level === l
                  ? "bg-accent-500 text-white"
                  : "bg-gray-800 text-gray-400 hover:text-gray-200"
              }`}
            >
              {l || "ALL"}
            </button>
          ))}
        </div>
        <span className="ml-auto text-xs text-gray-600">Últimos 200 logs</span>
      </div>

      <div
        ref={scrollRef}
        className="max-h-64 overflow-y-auto rounded-xl border border-gray-800 bg-gray-950 p-3 font-mono text-xs"
      >
        {(logs ?? []).length === 0 && (
          <p className="py-8 text-center text-gray-600">Sin logs</p>
        )}
        {(logs ?? []).map((log: any, i: number) => (
          <div key={i} className="flex items-start gap-2 py-0.5">
            <span className="shrink-0 text-gray-600">
              {log.timestamp
                ? new Date(log.timestamp).toLocaleTimeString()
                : ""}
            </span>
            {log.level && (
              <Badge variant={levelBadge[log.level] ?? "default"} className="shrink-0">
                {log.level}
              </Badge>
            )}
            <span className="text-gray-400">
              {log.event ?? log.message ?? JSON.stringify(log)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
