import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";

interface AuthState {
  authenticated: boolean;
  needsSetup: boolean;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    authenticated: false,
    needsSetup: false,
    loading: true,
  });

  const checkAuth = useCallback(async () => {
    try {
      const res = await fetch("/api/auth/status", {
        credentials: "include",
      });
      if (!res.ok) {
        setState({ authenticated: false, needsSetup: false, loading: false });
        return;
      }
      const data = await res.json();
      if (data.needs_setup) {
        setState({ authenticated: false, needsSetup: true, loading: false });
        return;
      }
      setState({ authenticated: data.authenticated, needsSetup: false, loading: false });
    } catch {
      setState({ authenticated: false, needsSetup: false, loading: false });
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback(async (password: string) => {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ password }),
    });
    if (!res.ok) throw new Error("Credenciales inválidas");
    setState({ authenticated: true, needsSetup: false, loading: false });
  }, []);

  const logout = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    setState({ authenticated: false, needsSetup: false, loading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
