import { useAboutInfo } from "@/services/queries";
import Skeleton from "@/components/Skeleton";
import { Info, Cpu, Globe } from "lucide-react";

export default function AboutPage() {
  const { data: about, isLoading } = useAboutInfo();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">About</h1>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">About</h1>

      <div className="max-w-lg space-y-4">
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
          <div className="mb-4 flex items-center gap-3">
            <span className="text-accent-500 text-3xl font-bold">TikDown</span>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <span className="flex items-center gap-2 text-gray-400">
                <Info className="h-4 w-4" />
                App version
              </span>
              <span className="text-gray-200 font-mono">
                {about?.app_version ?? "—"}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <span className="flex items-center gap-2 text-gray-400">
                <Globe className="h-4 w-4" />
                yt-dlp
              </span>
              <span className="text-gray-200 font-mono">
                {about?.yt_dlp_version ?? "—"}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <span className="flex items-center gap-2 text-gray-400">
                <Cpu className="h-4 w-4" />
                Stack
              </span>
              <span className="text-gray-200 font-mono text-xs text-right">
                {about?.stack ?? "Python / FastAPI / React / Tailwind"}
              </span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-800 bg-gray-900 p-4 text-xs text-gray-500">
          <p>
            TikDown es una aplicación web single-user que monitoriza cuentas de TikTok,
            descarga su historial completo y vigila el feed en busca de vídeos nuevos.
          </p>
        </div>
      </div>
    </div>
  );
}
