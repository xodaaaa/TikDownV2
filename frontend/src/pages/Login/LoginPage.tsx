import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) {
      setError("Introduce tu contraseña");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await login(password);
      navigate("/");
    } catch {
      setError("Contraseña incorrecta");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 p-4">
      <div className="w-full max-w-sm rounded-xl border border-gray-800 bg-gray-900 p-8">
        <div className="mb-6 text-center">
          <span className="text-accent-500 text-2xl font-bold">TikDown</span>
          <p className="text-gray-500 mt-1 text-sm">
            Introduce tu contraseña para continuar
          </p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 p-2.5 text-sm text-gray-200 placeholder-gray-600"
            placeholder="Contraseña"
            autoFocus
            disabled={loading}
          />
          {error && (
            <p className="text-red-400 text-xs">{error}</p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="bg-accent-500 hover:bg-accent-600 w-full rounded-lg py-2.5 text-sm font-medium text-white disabled:opacity-50 transition-colors"
          >
            {loading ? "Verificando..." : "Iniciar sesión"}
          </button>
        </form>
      </div>
    </div>
  );
}
