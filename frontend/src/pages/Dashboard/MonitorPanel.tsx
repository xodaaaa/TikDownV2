import { Play, Square, RefreshCw, Activity } from "lucide-react";
import Button from "@/components/Button";
import Badge from "@/components/Badge";
import { useStartMonitor, useStopMonitor, useCheckNow, useMonitorStatus } from "@/services/queries";
import type { SystemHealth } from "@/types";

interface MonitorPanelProps {
  health?: SystemHealth | null;
}

export default function MonitorPanel({ health }: MonitorPanelProps) {
  const { data: monitorStatus } = useMonitorStatus();
  const startMutation = useStartMonitor();
  const stopMutation = useStopMonitor();
  const checkMutation = useCheckNow();

  const isRunning = monitorStatus?.status === "running";
  const isOnline = health?.network_status === "online";
  const interval = monitorStatus?.interval_minutes ?? 10;
  const accounts = monitorStatus?.active_accounts ?? 0;
  const concurrency = monitorStatus?.concurrency ?? 2;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="h-5 w-5 text-accent-400" />
          <h2 className="text-sm font-semibold text-gray-200">Monitor</h2>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => startMutation.mutate()}
            disabled={isRunning || startMutation.isPending}
          >
            <Play className="h-3.5 w-3.5" />
            Start
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => stopMutation.mutate()}
            disabled={!isRunning || stopMutation.isPending}
          >
            <Square className="h-3.5 w-3.5" />
            Stop
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => checkMutation.mutate()}
            disabled={checkMutation.isPending}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${checkMutation.isPending ? "animate-spin" : ""}`} />
            Check Now
          </Button>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-gray-500">
        <span>
          Estado:{" "}
          <Badge variant={isRunning ? "success" : "default"}>
            {isRunning ? "Running" : "Stopped"}
          </Badge>
        </span>
        <span>Intervalo: {interval}m</span>
        <span>Cuentas: {accounts}</span>
        <span>Concurrencia: {concurrency}</span>
        <span>
          Red:{" "}
          <span
            className={`inline-flex items-center gap-1 font-medium ${
              isOnline ? "text-emerald-400" : "text-red-400"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isOnline ? "bg-emerald-400" : "bg-red-400"
              }`}
            />
            {isOnline ? "Online" : "Offline"}
          </span>
        </span>
      </div>
    </div>
  );
}
