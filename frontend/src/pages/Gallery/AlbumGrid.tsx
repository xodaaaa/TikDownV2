import AlbumCard from "./AlbumCard";
import EmptyState from "@/components/EmptyState";
import { Users } from "lucide-react";
import type { MonitoredAccount } from "@/types";

interface AlbumGridProps {
  accounts: MonitoredAccount[];
  videoCounts: Record<string, number>;
  onAlbumClick: (account: MonitoredAccount) => void;
}

export default function AlbumGrid({ accounts, videoCounts, onAlbumClick }: AlbumGridProps) {
  if (accounts.length === 0) {
    return (
      <EmptyState
        icon={Users}
        title="Sin álbumes"
        description="Añade cuentas para ver sus álbumes."
      />
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {accounts.map((acc) => (
        <AlbumCard
          key={acc.id}
          account={acc}
          videoCount={videoCounts[acc.id] ?? 0}
          onClick={() => onAlbumClick(acc)}
        />
      ))}
    </div>
  );
}
