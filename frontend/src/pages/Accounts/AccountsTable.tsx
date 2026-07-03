import { useState } from "react";
import { MoreVertical, UserCheck, UserX, RefreshCw, Download, Trash2 } from "lucide-react";
import Badge from "@/components/Badge";
import Button from "@/components/Button";
import BackfillBadge from "./BackfillBadge";
import { formatNumber } from "@/utils/format";
import { formatRelative } from "@/utils/date";
import { useDeleteAccount } from "@/services/queries";
import type { MonitoredAccount } from "@/types";

interface AccountsTableProps {
  accounts: MonitoredAccount[];
  onAddClick: () => void;
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

function AccountMenu({ account }: { account: MonitoredAccount }) {
  const [open, setOpen] = useState(false);
  const deleteMutation = useDeleteAccount();

  const handleDelete = () => {
    if (confirm(`¿Eliminar ${account.tiktok_username} y todos sus vídeos?`)) {
      deleteMutation.mutate(account.id);
    }
    setOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="rounded-lg p-1 text-gray-500 hover:bg-gray-800 hover:text-gray-200"
      >
        <MoreVertical className="h-4 w-4" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-1 w-48 rounded-lg border border-gray-700 bg-gray-900 py-1 shadow-xl">
            <button className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-800">
              <UserX className="h-4 w-4" />
              {account.enabled ? "Disable" : "Enable"}
            </button>
            <button className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-800">
              <RefreshCw className="h-4 w-4" />
              Rescan now
            </button>
            <button className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-800">
              <Download className="h-4 w-4" />
              Descargar historial
            </button>
            <hr className="border-gray-800" />
            <button
              onClick={handleDelete}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-400 hover:bg-gray-800"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default function AccountsTable({ accounts, onAddClick }: AccountsTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 bg-gray-900/50">
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Avatar
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Username
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Followers
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Backfill
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Last Check
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {accounts.map((acc) => (
            <tr key={acc.id} className="hover:bg-gray-900/50">
              <td className="px-4 py-3">
                <div className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full bg-gray-800">
                  {acc.avatar_url ? (
                    <img src={acc.avatar_url} alt="" className="h-8 w-8 object-cover" />
                  ) : (
                    <UserCheck className="h-4 w-4 text-gray-500" />
                  )}
                </div>
              </td>
              <td className="px-4 py-3 font-medium text-gray-200">
                @{acc.tiktok_username}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={acc.status} />
              </td>
              <td className="px-4 py-3 text-gray-400">
                {formatNumber(acc.follower_count)}
              </td>
              <td className="px-4 py-3">
                <BackfillBadge
                  status={acc.backfill_status}
                  done={acc.backfill_done}
                  total={acc.backfill_total}
                />
              </td>
              <td className="px-4 py-3 text-gray-400">
                {acc.last_check_at ? formatRelative(acc.last_check_at) : "—"}
              </td>
              <td className="px-4 py-3 text-right">
                <AccountMenu account={acc} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {accounts.length === 0 && (
        <div className="py-12 text-center text-gray-500">
          <p>Sin cuentas todavía</p>
          <Button variant="primary" size="sm" className="mt-3" onClick={onAddClick}>
            Añadir primera cuenta
          </Button>
        </div>
      )}
    </div>
  );
}
