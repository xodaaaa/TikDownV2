import Badge from "@/components/Badge";
import ProgressBar from "@/components/ProgressBar";
import type { MonitoredAccount } from "@/types";

interface BackfillBadgeProps {
  status: MonitoredAccount["backfill_status"];
  done?: number;
  total?: number;
}

export default function BackfillBadge({ status, done, total }: BackfillBadgeProps) {
  switch (status) {
    case "idle":
      return <Badge variant="default">○ idle</Badge>;
    case "backfilling":
      return (
        <div className="flex flex-col gap-1">
          <Badge variant="warning">◐ backfill {done ?? 0}/{total ?? "?"}</Badge>
          {total != null && total > 0 && (
            <ProgressBar value={done ?? 0} max={total} showCount={false} className="w-24" />
          )}
        </div>
      );
    case "paused":
      return <Badge variant="warning">⏸ paused</Badge>;
    case "completed":
      return <Badge variant="success">✓ done ({done ?? 0})</Badge>;
    case "cancelled":
      return <Badge variant="danger">✗ cancelled</Badge>;
    default:
      return <Badge variant="default">○ idle</Badge>;
  }
}
