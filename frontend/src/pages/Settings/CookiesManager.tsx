import { useState, useRef, useCallback } from "react";
import { Upload, Trash2, RefreshCw, Clock, FileText } from "lucide-react";
import Badge from "@/components/Badge";
import Button from "@/components/Button";
import { useCookies, useUploadCookie, useTestCookie, useDeleteCookie } from "@/services/queries";
import Skeleton from "@/components/Skeleton";

interface Cookie {
  id: string;
  original_format: "txt" | "json";
  status: "valid" | "unverified" | "invalid" | "expired";
  expires_at?: string;
  last_verified_at?: string;
  created_at: string;
}

const cookieStatusConfig: Record<
  Cookie["status"],
  { variant: "success" | "warning" | "danger" | "default"; label: string }
> = {
  valid: { variant: "success", label: "valid" },
  unverified: { variant: "warning", label: "unverified" },
  invalid: { variant: "danger", label: "invalid" },
  expired: { variant: "danger", label: "expired" },
};

function daysUntil(iso?: string): string {
  if (!iso) return "∞";
  const now = Date.now();
  const exp = new Date(iso).getTime();
  const diff = exp - now;
  if (diff <= 0) return "0";
  return `${Math.ceil(diff / (1000 * 60 * 60 * 24))}d`;
}

export default function CookiesManager() {
  const { data: cookies, isLoading } = useCookies();
  const uploadMutation = useUploadCookie();
  const testMutation = useTestCookie();
  const deleteMutation = useDeleteCookie();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.name.endsWith(".txt") && !file.name.endsWith(".json")) return;
      const formData = new FormData();
      formData.append("file", file);
      uploadMutation.mutate(formData);
    },
    [uploadMutation],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => setDragging(false);

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-20 rounded-xl" />
        <Skeleton className="h-12 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 transition-colors ${
          dragging
            ? "border-accent-500 bg-accent-500/5"
            : "border-gray-700 hover:border-gray-600"
        }`}
      >
        <Upload
          className={`mb-2 h-6 w-6 ${dragging ? "text-accent-400" : "text-gray-500"}`}
        />
        <p className="text-sm text-gray-400">
          Arrastra tu archivo .txt o .json aquí
        </p>
        <p className="mt-1 text-xs text-gray-600">o haz clic para seleccionar</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.json"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </div>

      <div className="space-y-2">
        {(cookies ?? []).length === 0 && (
          <p className="py-4 text-center text-xs text-gray-600">
            Sin cookies. Sube una para empezar.
          </p>
        )}
        {(cookies ?? []).map((cookie: Cookie) => {
          const cfg = cookieStatusConfig[cookie.status];
          return (
            <div
              key={cookie.id}
              className="flex items-center gap-3 rounded-lg border border-gray-800 bg-gray-900 px-4 py-3"
            >
              <FileText className="h-4 w-4 text-gray-500" />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-200">
                    {cookie.original_format === "txt" ? "cookies.txt" : "cookies.json"}
                  </span>
                  <Badge variant={cfg.variant}>{cfg.label}</Badge>
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <Clock className="h-3 w-3" />
                    {daysUntil(cookie.expires_at)}
                  </span>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => testMutation.mutate(cookie.id)}
                disabled={testMutation.isPending}
              >
                <RefreshCw
                  className={`h-3.5 w-3.5 ${testMutation.isPending ? "animate-spin" : ""}`}
                />
                Probar
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  if (confirm("¿Eliminar esta cookie?")) {
                    deleteMutation.mutate(cookie.id);
                  }
                }}
              >
                <Trash2 className="h-3.5 w-3.5 text-red-400" />
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
