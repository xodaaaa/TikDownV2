import VideoCard from "./VideoCard";
import EmptyState from "@/components/EmptyState";
import { Film } from "lucide-react";
import type { Video } from "@/types";

interface VideoGridProps {
  videos: Video[];
  onVideoClick: (video: Video) => void;
}

export default function VideoGrid({ videos, onVideoClick }: VideoGridProps) {
  if (videos.length === 0) {
    return (
      <EmptyState
        icon={Film}
        title="Sin vídeos"
        description="Los vídeos descargados aparecerán aquí."
      />
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {videos.map((video) => (
        <VideoCard key={video.id} video={video} onClick={onVideoClick} />
      ))}
    </div>
  );
}
