import { User, Film } from "lucide-react";
import Badge from "@/components/Badge";
import { formatRelative } from "@/utils/date";
import type { MonitoredAccount } from "@/types";

interface AlbumCardProps {
  account: MonitoredAccount;
  videoCount: number;
  onClick: () => void;
}

function StatusBadge({ status }: { status: MonitoredAccount["status"] }) {
  const map: Record<MonitoredAccount["status"], { variant: "success" | "warning" | "danger"; label: string }> = {
    ok: { variant: "success", label: "ok" },
    needs_review: { variant: "warning", label: "needs_review" },
    paused: { variant: "danger", label: "paused" },
  };
  const { variant, label } = map[status];
  return <Badge variant={variant}>● {label}</Badge>;
}

export default function AlbumCard({ account, videoCount, onClick }: AlbumCardProps) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center gap-3 rounded-xl border border-gray-800 bg-gray-900 p-6 transition-colors hover:border-gray-700"
    >
      <div className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-gray-800">
        {account.avatar_url ? (
          <img src={account.avatar_url} alt="" className="h-16 w-16 object-cover" />
        ) : (
          <User className="h-8 w-8 text-gray-500" />
        )}
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-gray-200">@{account.tiktok_username}</p>
        <p className="mt-1 flex items-center justify-center gap-1 text-xs text-gray-500">
          <Film className="h-3.5 w-3.5" />
          {videoCount} vídeos
        </p>
      </div>
      <StatusBadge status={account.status} />
      {account.last_check_at && (
        <p className="text-xs text-gray-600">últ: {formatRelative(account.last_check_at)}</p>
      )}
    </button>
  );
}
