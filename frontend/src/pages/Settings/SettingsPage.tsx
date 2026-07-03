import { useState, useEffect, useRef } from "react";
import { Bell, Monitor, Cookie, FileText } from "lucide-react";
import CookiesManager from "./CookiesManager";
import LogsViewer from "./LogsViewer";
import Button from "@/components/Button";
import { toast } from "@/components/Toast";
import { useUpdateSettings } from "@/services/queries";

function DebouncedInput({
  label,
  hint,
  type = "number",
  min,
  defaultValue,
  onSave,
}: {
  label: string;
  hint?: string;
  type?: string;
  min?: number;
  defaultValue: number;
  onSave: (val: number) => void;
}) {
  const [value, setValue] = useState(defaultValue);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setValue(defaultValue);
  }, [defaultValue]);

  const handleChange = (newVal: number) => {
    setValue(newVal);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      onSave(newVal);
      toast("Guardado", "success");
    }, 1000);
  };

  return (
    <div>
      <label className="text-gray-400 mb-1 block text-sm">{label}</label>
      <input
        type={type}
        min={min}
        value={value}
        onChange={(e) => handleChange(Number(e.target.value))}
        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200"
      />
      {hint && <p className="text-gray-600 mt-1 text-xs">{hint}</p>}
    </div>
  );
}

export default function SettingsPage() {
  const updateSettings = useUpdateSettings();
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [telegramToken, setTelegramToken] = useState("");
  const [telegramChatId, setTelegramChatId] = useState("");
  const [botMode, setBotMode] = useState<"notifications" | "commands" | "both">("notifications");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const autoSave = (data: Record<string, unknown>) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      updateSettings.mutate(data);
      toast("Guardado", "success");
    }, 1000);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <section className="rounded-xl border border-gray-800 bg-gray-900 p-4">
            <div className="mb-4 flex items-center gap-2">
              <Monitor className="h-5 w-5 text-accent-400" />
              <h2 className="text-sm font-semibold text-gray-200">
                Monitor Preferences
              </h2>
            </div>
            <div className="space-y-4">
              <DebouncedInput
                label="Intervalo (minutos)"
                hint="Mínimo 5 min"
                min={5}
                defaultValue={10}
                onSave={(v) => autoSave({ monitor_interval: v })}
              />
              <DebouncedInput
                label="Concurrencia máxima"
                min={1}
                defaultValue={2}
                onSave={(v) => autoSave({ max_concurrent_downloads: v })}
              />
              <DebouncedInput
                label="Delay mínimo (segundos)"
                hint="Jitter aleatorio entre delay min y max"
                min={1}
                defaultValue={10}
                onSave={(v) => autoSave({ min_delay: v })}
              />
              <DebouncedInput
                label="Delay máximo (segundos)"
                min={1}
                defaultValue={60}
                onSave={(v) => autoSave({ max_delay: v })}
              />
              <div>
                <label className="text-gray-400 mb-1 block text-sm">Calidad</label>
                <p className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-500">
                  best (no editable)
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-xl border border-gray-800 bg-gray-900 p-4">
            <div className="mb-4 flex items-center gap-2">
              <Bell className="h-5 w-5 text-accent-400" />
              <h2 className="text-sm font-semibold text-gray-200">
                Notifications
              </h2>
            </div>
            <div className="space-y-4">
              <label className="flex items-center gap-2 text-sm text-gray-300">
                <input
                  type="checkbox"
                  checked={notificationsEnabled}
                  onChange={(e) => {
                    setNotificationsEnabled(e.target.checked);
                    autoSave({ enable_external_notifications: e.target.checked });
                  }}
                  className="rounded border-gray-700 bg-gray-800 text-accent-500"
                />
                Enable external notifications
              </label>

              {notificationsEnabled && (
                <>
                  <div>
                    <label className="text-gray-400 mb-1 block text-sm">
                      Telegram
                    </label>
                    <div className="space-y-2">
                      <input
                        value={telegramToken}
                        onChange={(e) => {
                          setTelegramToken(e.target.value);
                          autoSave({ telegram_bot_token: e.target.value });
                        }}
                        placeholder="Bot Token"
                        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-600"
                      />
                      <input
                        value={telegramChatId}
                        onChange={(e) => {
                          setTelegramChatId(e.target.value);
                          autoSave({ telegram_chat_id: e.target.value });
                        }}
                        placeholder="Chat ID"
                        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-600"
                      />
                    </div>
                  </div>

                  {telegramToken && telegramChatId && (
                    <div>
                      <label className="text-gray-400 mb-2 block text-sm">Modo del bot</label>
                      <div className="space-y-2">
                        {(["notifications", "commands", "both"] as const).map((mode) => (
                          <label
                            key={mode}
                            className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 ${
                              botMode === mode
                                ? "border-accent-500 bg-accent-500/5"
                                : "border-gray-700"
                            }`}
                          >
                            <input
                              type="radio"
                              name="botMode"
                              value={mode}
                              checked={botMode === mode}
                              onChange={() => {
                                setBotMode(mode);
                                autoSave({ telegram_bot_mode: mode });
                              }}
                              className="text-accent-500"
                            />
                            <span className="text-sm text-gray-300">
                              {mode === "notifications" && "Solo notificaciones"}
                              {mode === "commands" && "Solo comandos"}
                              {mode === "both" && "Ambos"}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  <Button variant="secondary" size="sm">
                    Probar Telegram
                  </Button>
                </>
              )}
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section className="rounded-xl border border-gray-800 bg-gray-900 p-4">
            <div className="mb-4 flex items-center gap-2">
              <Cookie className="h-5 w-5 text-accent-400" />
              <h2 className="text-sm font-semibold text-gray-200">
                Cookies Manager
              </h2>
            </div>
            <CookiesManager />
          </section>

          <section className="rounded-xl border border-gray-800 bg-gray-900 p-4">
            <div className="mb-4 flex items-center gap-2">
              <FileText className="h-5 w-5 text-accent-400" />
              <h2 className="text-sm font-semibold text-gray-200">Logs</h2>
            </div>
            <LogsViewer />
          </section>
        </div>
      </div>
    </div>
  );
}
