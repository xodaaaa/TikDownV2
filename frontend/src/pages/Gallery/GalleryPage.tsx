import { useState, useMemo } from "react";
import { Search, ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import VideoGrid from "./VideoGrid";
import VideoModal from "./VideoModal";
import AlbumGrid from "./AlbumGrid";
import Button from "@/components/Button";
import { useVideos, useAccounts } from "@/services/queries";
import Skeleton from "@/components/Skeleton";
import type { Video, MonitoredAccount } from "@/types";

type ViewMode = "all" | "albums";

export default function GalleryPage() {
  const { data: accounts, isLoading: accountsLoading } = useAccounts();
  const { data: videos, isLoading: videosLoading } = useVideos();
  const [view, setView] = useState<ViewMode>("albums");
  const [selectedAccount, setSelectedAccount] = useState<MonitoredAccount | null>(null);
  const [modalVideo, setModalVideo] = useState<Video | null>(null);
  const [searchAuthor, setSearchAuthor] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [page, setPage] = useState(1);
  const perPage = 20;

  const videoCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    (videos ?? []).forEach((v: Video) => {
      counts[v.monitored_account_id] = (counts[v.monitored_account_id] ?? 0) + 1;
    });
    return counts;
  }, [videos]);

  const displayView: ViewMode =
    view === "albums" && (accounts?.length ?? 0) <= 1 ? "all" : view;

  const filteredVideos = useMemo(() => {
    let list = videos ?? [];
    if (selectedAccount) {
      list = list.filter((v: Video) => v.monitored_account_id === selectedAccount.id);
    }
    if (searchAuthor) {
      list = list.filter((v: Video) =>
        v.monitored_account_id.toLowerCase().includes(searchAuthor.toLowerCase()),
      );
    }
    if (statusFilter) {
      list = list.filter((v: Video) => v.status === statusFilter);
    }
    return list as Video[];
  }, [videos, selectedAccount, searchAuthor, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredVideos.length / perPage));
  const pagedVideos = filteredVideos.slice((page - 1) * perPage, page * perPage);

  const handleAlbumClick = (acc: MonitoredAccount) => {
    setSelectedAccount(acc);
    setView("all");
    setPage(1);
  };

  const handleBackToAlbums = () => {
    setSelectedAccount(null);
    setView("albums");
    setPage(1);
  };

  if (accountsLoading || videosLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Gallery</h1>
        <Skeleton className="h-10 w-96 rounded-xl" />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="aspect-[9/16] rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {selectedAccount ? (
            <button
              onClick={handleBackToAlbums}
              className="rounded-lg p-1 text-gray-500 hover:text-gray-200"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
          ) : null}
          <h1 className="text-2xl font-bold">
            {selectedAccount
              ? `Gallery › @${selectedAccount.tiktok_username}`
              : "Gallery"}
          </h1>
        </div>

        {!selectedAccount && (
          <div className="flex items-center gap-1 rounded-lg border border-gray-800 bg-gray-900 p-1">
            <button
              onClick={() => {
                setView("all");
                setPage(1);
              }}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                displayView === "all"
                  ? "bg-accent-500 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Todos
            </button>
            <button
              onClick={() => {
                setView("albums");
                setPage(1);
              }}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                displayView === "albums"
                  ? "bg-accent-500 text-white"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Álbumes
            </button>
          </div>
        )}
      </div>

      {displayView === "all" ? (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <input
                value={searchAuthor}
                onChange={(e) => {
                  setSearchAuthor(e.target.value);
                  setPage(1);
                }}
                placeholder="Filtrar por autor..."
                className="w-full rounded-lg border border-gray-700 bg-gray-800 py-2 pl-9 pr-3 text-sm text-gray-200 placeholder-gray-600"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200"
            >
              <option value="">Todos los estados</option>
              <option value="downloaded">Descargado</option>
              <option value="downloading">Descargando</option>
              <option value="queued">En cola</option>
              <option value="failed">Error</option>
            </select>
          </div>

          <VideoGrid videos={pagedVideos} onVideoClick={setModalVideo} />

          {filteredVideos.length > 0 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-xs text-gray-500">
                Página {page} de {totalPages}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
              <select
                value={perPage}
                className="ml-2 rounded-lg border border-gray-700 bg-gray-800 px-2 py-1 text-xs text-gray-400"
              >
                <option value={20}>20 / pág</option>
                <option value={40}>40 / pág</option>
                <option value={60}>60 / pág</option>
              </select>
            </div>
          )}
        </div>
      ) : (
        <AlbumGrid
          accounts={accounts ?? []}
          videoCounts={videoCounts}
          onAlbumClick={handleAlbumClick}
        />
      )}

      {modalVideo && (
        <VideoModal video={modalVideo} onClose={() => setModalVideo(null)} />
      )}
    </div>
  );
}
