import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type { Video, MonitoredAccount, SystemHealth, ActivityEvent } from "@/types";

export function useVideos(params?: { accountId?: string; status?: string; page?: number; perPage?: number }) {
  const searchParams = new URLSearchParams();
  if (params?.accountId) searchParams.set("account_id", params.accountId);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.perPage) searchParams.set("per_page", String(params.perPage));
  const qs = searchParams.toString();
  return useQuery({
    queryKey: ["videos", params],
    queryFn: () => api.get<Video[]>(`/api/videos${qs ? `?${qs}` : ""}`),
  });
}

export function useVideo(id: string) {
  return useQuery({
    queryKey: ["videos", id],
    queryFn: () => api.get<Video>(`/api/videos/${id}`),
    enabled: !!id,
  });
}

export function useAccounts() {
  return useQuery({
    queryKey: ["accounts"],
    queryFn: () => api.get<MonitoredAccount[]>("/api/accounts"),
  });
}

export function useAccount(id: string) {
  return useQuery({
    queryKey: ["accounts", id],
    queryFn: () => api.get<MonitoredAccount>(`/api/accounts/${id}`),
    enabled: !!id,
  });
}

export function useAccountMetrics() {
  return useQuery({
    queryKey: ["accounts", "metrics"],
    queryFn: () => api.get<any>("/api/system/metrics"),
  });
}

export function useCookies() {
  return useQuery({
    queryKey: ["cookies"],
    queryFn: () => api.get<any[]>("/api/cookies"),
  });
}

export function useEvents(limit = 50) {
  return useQuery({
    queryKey: ["events", limit],
    queryFn: () => api.get<ActivityEvent[]>(`/api/events?limit=${limit}`),
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: ["system", "health"],
    queryFn: () => api.get<SystemHealth>("/api/system/health"),
    refetchInterval: 30_000,
  });
}

export function useMonitorStatus() {
  return useQuery({
    queryKey: ["monitor", "status"],
    queryFn: () => api.get<any>("/api/monitor/status"),
    refetchInterval: 15_000,
  });
}

export function useLogs(level?: string) {
  const searchParams = new URLSearchParams();
  searchParams.set("limit", "200");
  if (level) searchParams.set("level", level);
  return useQuery({
    queryKey: ["logs", level],
    queryFn: () => api.get<any[]>(`/api/system/logs?${searchParams.toString()}`),
  });
}

export function useAddAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { tiktok_username: string; capture_mode: string }) =>
      api.post("/api/accounts", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });
}

export function useDeleteAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/accounts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });
}

export function useStartMonitor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/api/monitor/start"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["monitor"] });
      queryClient.invalidateQueries({ queryKey: ["system"] });
    },
  });
}

export function useStopMonitor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/api/monitor/stop"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["monitor"] });
      queryClient.invalidateQueries({ queryKey: ["system"] });
    },
  });
}

export function useCheckNow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/api/monitor/check"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["videos"] });
    },
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (settings: Record<string, unknown>) => api.put("/api/settings", settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });
}

export function useUploadCookie() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) => api.upload("/api/cookies", formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cookies"] });
    },
  });
}

export function useTestCookie() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post(`/api/cookies/${id}/test`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cookies"] });
    },
  });
}

export function useDeleteCookie() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/cookies/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cookies"] });
    },
  });
}

export function useSetupWizard() {
  return useMutation({
    mutationFn: (data: { password: string; monitorInterval: number; cookieFile?: File }) => {
      const formData = new FormData();
      formData.append("password", data.password);
      formData.append("monitor_interval", String(data.monitorInterval));
      if (data.cookieFile) formData.append("cookie", data.cookieFile);
      return api.upload("/api/setup", formData);
    },
  });
}

export function useAboutInfo() {
  return useQuery({
    queryKey: ["system", "about"],
    queryFn: () => api.get<any>("/api/system/about"),
  });
}
