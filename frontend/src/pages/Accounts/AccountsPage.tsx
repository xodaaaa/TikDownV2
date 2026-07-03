import { useState } from "react";
import { Search, Plus } from "lucide-react";
import AccountsTable from "./AccountsTable";
import AddAccountModal from "./AddAccountModal";
import { useAccounts } from "@/services/queries";
import Skeleton from "@/components/Skeleton";
import EmptyState from "@/components/EmptyState";
import Button from "@/components/Button";
import type { MonitoredAccount } from "@/types";

export default function AccountsPage() {
  const { data: accounts, isLoading } = useAccounts();
  const [search, setSearch] = useState("");
  const [showDisabled, setShowDisabled] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const filtered = (accounts ?? []).filter((acc: MonitoredAccount) => {
    const matchesSearch = acc.tiktok_username.toLowerCase().includes(search.toLowerCase());
    const matchesDisabled = showDisabled || acc.enabled;
    return matchesSearch && matchesDisabled;
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Accounts</h1>
        <Skeleton className="h-10 w-full rounded-xl" />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Accounts</h1>
        <Button variant="primary" onClick={() => setModalOpen(true)}>
          <Plus className="h-4 w-4" />
          Add Account
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar cuenta..."
            className="w-full rounded-lg border border-gray-700 bg-gray-800 py-2 pl-9 pr-3 text-sm text-gray-200 placeholder-gray-600"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <input
            type="checkbox"
            checked={showDisabled}
            onChange={(e) => setShowDisabled(e.target.checked)}
            className="rounded border-gray-700 bg-gray-800 text-accent-500"
          />
          Mostrar deshabilitadas
        </label>
      </div>

      {filtered.length === 0 && accounts?.length === 0 ? (
        <EmptyState
          title="Sin cuentas"
          description="Añade tu primera cuenta de TikTok para empezar a monitorizar."
          action={<Button variant="primary" onClick={() => setModalOpen(true)}>Añadir cuenta</Button>}
        />
      ) : (
        <AccountsTable accounts={filtered} onAddClick={() => setModalOpen(true)} />
      )}

      <AddAccountModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
