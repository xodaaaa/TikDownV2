import { useEffect } from "react";
import { X, Heart, Eye, Download, RefreshCw, Trash2, AlertTriangle } from "lucide-react";
import Button from "@/components/Button";
import Badge from "@/components/Badge";
import { formatNumber } from "@/utils/format";
import { formatDate } from "@/utils/date";
import type { Video } from "@/types";

interface VideoModalProps {
  video: Video;
  onClose: () => void;
}

const errorSuggestions: Record<string, string> = {
  auth: "Re-importa las cookies desde el navegador",
  rate_limit: "Sube el intervalo mínimo",
  ip_block: "Verifica la reputación de tu IP de salida",
  network: "Reintentando automáticamente (transitorio)",
  not_found: "El vídeo fue borrado de TikTok",
};

export default function VideoModal({ video, onClose }: VideoModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const isDownloaded = video.status === "downloaded";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl border border-gray-800 bg-gray-900 shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-800 p-4">
          <h3 className="truncate text-lg font-semibold text-gray-200">
            {video.title || "Sin título"}
          </h3>
          <button onClick={onClose} className="rounded-lg p-1 text-gray-500 hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4 lg:flex-row">
          <div className="flex flex-col items-center lg:w-1/2">
            {isDownloaded ? (
              <video
                src={`/api/videos/${video.id}/file`}
                controls
                className="w-full rounded-lg bg-black"
                style={{ aspectRatio: "9/16", maxHeight: "60vh" }}
              >
                Tu navegador no soporta el reproductor de vídeo.
              </video>
            ) : (
              <div className="flex aspect-[9/16] w-full items-center justify-center rounded-lg bg-gray-800">
                {video.thumbnail_path ? (
                  <img src={video.thumbnail_path} alt="" className="h-full w-full object-cover rounded-lg" />
                ) : (
                  <div className="text-center text-gray-600">
                    <p className="text-sm font-medium">
                      {video.status === "queued" && "En cola"}
                      {video.status === "downloading" && "Descargando..."}
                      {video.status === "failed" && "Error"}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex flex-col gap-3 lg:w-1/2">
            <div className="space-y-1">
              <p className="text-sm text-gray-200">
                <span className="text-gray-500">Autor:</span> @{video.monitored_account_id}
              </p>
              <div className="flex items-center gap-3 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <Heart className={`h-4 w-4 ${(video.likes ?? 0) > 0 ? "text-red-400" : ""}`} />
                  {formatNumber(video.likes)}
                </span>
                <span className="flex items-center gap-1">
                  <Eye className="h-4 w-4" />
                  {formatNumber(video.views)}
                </span>
              </div>
              {video.upload_date && (
                <p className="text-sm text-gray-500">
                  <span className="text-gray-500">Fecha:</span> {formatDate(video.upload_date)}
                </p>
              )}
              {video.duration != null && video.duration > 0 && (
                <p className="text-sm text-gray-500">
                  <span className="text-gray-500">Duración:</span> {Math.floor(video.duration / 60)}:
                  {(video.duration % 60).toString().padStart(2, "0")}
                </p>
              )}
              {video.file_size != null && (
                <p className="text-sm text-gray-500">
                  <span className="text-gray-500">Tamaño:</span>{" "}
                  {(video.file_size / 1024 / 1024).toFixed(1)} MB
                </p>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Badge
                variant={
                  video.status === "downloaded"
                    ? "success"
                    : video.status === "failed"
                      ? "danger"
                      : video.status === "downloading"
                        ? "warning"
                        : "default"
                }
              >
                {video.status}
              </Badge>
              {video.error_kind && (
                <Badge variant="danger">{video.error_kind}</Badge>
              )}
            </div>

            {video.status === "failed" && video.error_text && (
              <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                <div>
                  <p className="text-xs text-red-400">{video.error_text}</p>
                  {video.error_kind && errorSuggestions[video.error_kind] && (
                    <p className="text-red-400/70 mt-1 text-xs">
                      Sugerencia: {errorSuggestions[video.error_kind]}
                    </p>
                  )}
                </div>
              </div>
            )}

            <div className="mt-auto flex flex-col gap-2">
              {!isDownloaded && video.status !== "failed" && (
                <Button variant="secondary" disabled>
                  <Download className="h-4 w-4" />
                  Reproducir (no descargado)
                </Button>
              )}
              {video.status !== "downloaded" && (
                <Button variant="secondary">
                  <RefreshCw className="h-4 w-4" />
                  Redownload
                </Button>
              )}
              {isDownloaded && (
                <>
                  <Button variant="secondary">
                    <Download className="h-4 w-4" />
                    Download
                  </Button>
                  <Button variant="secondary">
                    <RefreshCw className="h-4 w-4" />
                    Redownload
                  </Button>
                </>
              )}
              <Button
                variant="danger"
                onClick={() => {
                  if (confirm(`¿Eliminar este vídeo?`)) {
                    onClose();
                  }
                }}
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
