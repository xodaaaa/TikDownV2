import { format, formatDistanceToNow, parseISO } from "date-fns";
import { es } from "date-fns/locale";

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return format(parseISO(iso), "dd MMM yyyy", { locale: es });
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return format(parseISO(iso), "dd MMM yyyy HH:mm", { locale: es });
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return "—";
  return formatDistanceToNow(parseISO(iso), { addSuffix: true, locale: es });
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = parseISO(iso);
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return format(d, "HH:mm:ss", { locale: es }) + ` (${tz})`;
}
