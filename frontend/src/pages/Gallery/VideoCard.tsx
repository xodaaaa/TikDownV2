import { Heart, Play } from "lucide-react";
import Badge from "@/components/Badge";
import { formatNumber } from "@/utils/format";
import type { Video } from "@/types";

interface VideoCardProps {
  video: Video;
  onClick: (video: Video) => void;
}

const statusConfig: Record<Video["status"], { variant: "success" | "warning" | "danger" | "default"; label: string }> = {
  downloaded: { variant: "success", label: "downloaded" },
  downloading: { variant: "warning", label: "downloading" },
  queued: { variant: "default", label: "queued" },
  failed: { variant: "danger", label: "failed" },
};

export default function VideoCard({ video, onClick }: VideoCardProps) {
  const cfg = statusConfig[video.status];

  return (
    <button
      onClick={() => onClick(video)}
      className="group relative flex flex-col overflow-hidden rounded-xl border border-gray-800 bg-gray-900 text-left transition-colors hover:border-gray-700"
    >
      <div className="relative aspect-[9/16] w-full overflow-hidden bg-gray-800">
        {video.thumbnail_path ? (
          <img
            src={video.thumbnail_path}
            alt=""
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <Play className="h-10 w-10 text-gray-600" />
          </div>
        )}
        <div className="absolute left-2 top-2">
          <Badge variant={cfg.variant}>{cfg.label}</Badge>
        </div>
      </div>

      <div className="flex flex-1 flex-col justify-between gap-1 p-2.5">
        <p className="line-clamp-2 text-sm leading-tight text-gray-200">
          {video.title || "Sin título"}
        </p>
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <Heart className={`h-3.5 w-3.5 ${(video.likes ?? 0) > 0 ? "text-red-400" : ""}`} />
          <span>{formatNumber(video.likes)}</span>
        </div>
      </div>
    </button>
  );
}
