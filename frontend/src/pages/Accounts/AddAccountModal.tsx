import { useState } from "react";
import { X, AlertTriangle } from "lucide-react";
import Button from "@/components/Button";
import { useAddAccount } from "@/services/queries";

interface AddAccountModalProps {
  open: boolean;
  onClose: () => void;
}

export default function AddAccountModal({ open, onClose }: AddAccountModalProps) {
  const [username, setUsername] = useState("");
  const [mode, setMode] = useState<"history_and_monitor" | "monitor_only">("history_and_monitor");
  const addMutation = useAddAccount();

  if (!open) return null;

  const handleAdd = () => {
    const clean = username.replace(/^@/, "").trim();
    if (!clean) return;
    addMutation.mutate(
      { tiktok_username: clean, capture_mode: mode },
      {
        onSuccess: () => {
          setUsername("");
          setMode("history_and_monitor");
          onClose();
        },
      },
    );
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
    >
      <div className="w-full max-w-md rounded-xl border border-gray-800 bg-gray-900 p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-200">Añadir cuenta</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-gray-500 hover:text-gray-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-gray-400 mb-1 block text-sm">Usuario de TikTok</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="@usuario"
              className="w-full rounded-lg border border-gray-700 bg-gray-800 p-2.5 text-sm text-gray-200 placeholder-gray-600"
              autoFocus
            />
          </div>

          <div>
            <label className="text-gray-400 mb-2 block text-sm">Modo de captura</label>
            <div className="space-y-2">
              <label
                className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors ${
                  mode === "history_and_monitor"
                    ? "border-accent-500 bg-accent-500/5"
                    : "border-gray-700 hover:border-gray-600"
                }`}
              >
                <input
                  type="radio"
                  name="mode"
                  value="history_and_monitor"
                  checked={mode === "history_and_monitor"}
                  onChange={() => setMode("history_and_monitor")}
                  className="mt-0.5 text-accent-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-200">
                    Historial + Monitor <span className="text-accent-400 text-xs">(recomendado)</span>
                  </span>
                  <p className="text-gray-500 text-xs">
                    Descarga todo el historial primero, luego vigila el feed.
                  </p>
                </div>
              </label>

              <label
                className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors ${
                  mode === "monitor_only"
                    ? "border-accent-500 bg-accent-500/5"
                    : "border-gray-700 hover:border-gray-600"
                }`}
              >
                <input
                  type="radio"
                  name="mode"
                  value="monitor_only"
                  checked={mode === "monitor_only"}
                  onChange={() => setMode("monitor_only")}
                  className="mt-0.5 text-accent-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-200">Solo Monitor</span>
                  <p className="text-gray-500 text-xs">
                    Vigila solo vídeos nuevos desde ahora. El historial previo NO se descarga.
                  </p>
                </div>
              </label>
            </div>
          </div>

          {mode === "monitor_only" && (
            <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
              <p className="text-amber-400 text-xs leading-relaxed">
                Si más tarde ejecutas "Descargar historial", el orden de descarga y la
                deduplicación pueden confundirte. La app previene duplicados por código
                (tiktok_id UNIQUE + download-archive), pero el flujo es más limpio si
                empiezas con Historial+Monitor.
              </p>
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            variant="primary"
            onClick={handleAdd}
            disabled={!username.trim() || addMutation.isPending}
          >
            {addMutation.isPending ? "Añadiendo..." : "Añadir"}
          </Button>
        </div>
      </div>
    </div>
  );
}
