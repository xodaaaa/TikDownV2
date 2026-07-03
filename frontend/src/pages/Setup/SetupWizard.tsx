import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Upload } from "lucide-react";
import { useSetupWizard } from "@/services/queries";

export default function SetupWizard() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [monitorInterval, setMonitorInterval] = useState(10);
  const [cookieFile, setCookieFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const setupMutation = useSetupWizard();

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && (file.name.endsWith(".txt") || file.name.endsWith(".json"))) {
      setCookieFile(file);
    }
  }, []);

  const handleFinish = () => {
    setupMutation.mutate(
      { password, monitorInterval, cookieFile: cookieFile ?? undefined },
      { onSuccess: () => navigate("/") },
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 p-4">
      <div className="w-full max-w-sm rounded-xl border border-gray-800 bg-gray-900 p-8">
        <div className="mb-6 text-center">
          <span className="text-accent-500 text-2xl font-bold">TikDown</span>
          <p className="text-gray-500 mt-1 text-sm">
            {step === 1 && "Paso 1/3 — Crea tu contraseña"}
            {step === 2 && "Paso 2/3 — Intervalo de monitor"}
            {step === 3 && "Paso 3/3 — Sube tu primera cookie (opcional)"}
          </p>
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className="text-gray-400 mb-1 block text-sm">Contraseña</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 p-2.5 text-sm text-gray-200 placeholder-gray-600"
                placeholder="Mínimo 8 caracteres"
                autoFocus
              />
            </div>
            <div>
              <label className="text-gray-400 mb-1 block text-sm">Confirmar contraseña</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 p-2.5 text-sm text-gray-200 placeholder-gray-600"
                placeholder="Repite la contraseña"
              />
            </div>
            {password && confirmPassword && password !== confirmPassword && (
              <p className="text-red-400 text-xs">Las contraseñas no coinciden</p>
            )}
            <button
              onClick={() => setStep(2)}
              disabled={password.length < 8 || password !== confirmPassword}
              className="bg-accent-500 hover:bg-accent-600 w-full rounded-lg py-2.5 text-sm font-medium text-white disabled:opacity-50 transition-colors"
            >
              Continuar
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div>
              <label className="text-gray-400 mb-1 block text-sm">
                Intervalo de monitor (minutos)
              </label>
              <input
                type="number"
                min={5}
                value={monitorInterval}
                onChange={(e) => setMonitorInterval(Number(e.target.value))}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 p-2.5 text-sm text-gray-200"
                autoFocus
              />
              <p className="text-gray-600 mt-1 text-xs">
                Mínimo 5 min · Recomendado 10 min
              </p>
            </div>
            <button
              onClick={() => setStep(3)}
              disabled={monitorInterval < 5}
              className="bg-accent-500 hover:bg-accent-600 w-full rounded-lg py-2.5 text-sm font-medium text-white disabled:opacity-50 transition-colors"
            >
              Continuar
            </button>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <div
              onDrop={handleDrop}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onClick={() => fileInputRef.current?.click()}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
                dragging ? "border-accent-500 bg-accent-500/5" : "border-gray-700 hover:border-gray-600"
              }`}
            >
              {cookieFile ? (
                <div className="text-center">
                  <Upload className="mx-auto mb-2 h-6 w-6 text-accent-400" />
                  <p className="text-sm text-accent-400">{cookieFile.name}</p>
                </div>
              ) : (
                <>
                  <Upload className="mb-2 h-6 w-6 text-gray-500" />
                  <p className="text-sm text-gray-400">
                    Arrastra tu archivo .txt o .json aquí
                  </p>
                  <p className="mt-1 text-xs text-gray-600">
                    o haz clic para seleccionar
                  </p>
                </>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.json"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) setCookieFile(file);
                }}
              />
            </div>
            <p className="text-gray-600 text-xs text-center">
              Opcional. Puedes subir cookies más tarde en Settings.
            </p>
            <button
              onClick={handleFinish}
              disabled={setupMutation.isPending}
              className="bg-accent-500 hover:bg-accent-600 w-full rounded-lg py-2.5 text-sm font-medium text-white disabled:opacity-50 transition-colors"
            >
              {setupMutation.isPending ? "Configurando..." : "Finalizar"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
