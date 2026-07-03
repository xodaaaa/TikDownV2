import { useEffect, useState, useCallback } from "react";
import { X } from "lucide-react";

export interface ToastData {
  id: string;
  message: string;
  type: "info" | "success" | "danger";
}

let toastIdCounter = 0;
let addToastFn: ((t: ToastData) => void) | null = null;

export function toast(message: string, type: ToastData["type"] = "info") {
  const id = `toast-${++toastIdCounter}`;
  addToastFn?.({ id, message, type });
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const addToast = useCallback((t: ToastData) => {
    setToasts((prev) => [...prev, t]);
  }, []);

  useEffect(() => {
    addToastFn = addToast;
    return () => {
      addToastFn = null;
    };
  }, [addToast]);

  const remove = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  useEffect(() => {
    const timers = toasts
      .filter((t) => t.type !== "danger")
      .map((t) =>
        setTimeout(() => remove(t.id), 5000),
      );
    return () => timers.forEach(clearTimeout);
  }, [toasts]);

  const typeStyles = {
    info: "border border-blue-500/30 bg-blue-500/10 text-blue-400",
    success: "border border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
    danger: "border border-red-500/30 bg-red-500/10 text-red-400",
  };

  return (
    <div className="fixed right-4 top-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm shadow-lg backdrop-blur-sm ${typeStyles[t.type]}`}
        >
          <span className="flex-1">{t.message}</span>
          <button
            onClick={() => remove(t.id)}
            className="shrink-0 opacity-60 hover:opacity-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
