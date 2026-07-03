import { Film, Users, Eye, Heart, HardDrive } from "lucide-react";
import { formatNumber, formatBytes } from "@/utils/format";
import type { SystemHealth, SystemMetrics } from "@/types";

interface DashboardCardsProps {
  health?: SystemHealth | null;
  metrics?: SystemMetrics | null;
}

interface CardData {
  label: string;
  value: string;
  sub?: string;
  icon: typeof Film;
  color: string;
}

function buildCards(health?: SystemHealth | null, metrics?: SystemMetrics | null): CardData[] {
  const totalVideos = 0;
  const totalAccounts = health?.accounts ?? metrics?.accounts_ok ?? 0;
  const totalViews = 0;
  const totalLikes = 0;
  const diskFree = health?.disk_free_gb ?? metrics?.disk_free_gb ?? 0;
  const diskTotal = metrics?.disk_total_gb ?? 0;

  return [
    {
      label: "Vídeos",
      value: formatNumber(totalVideos),
      icon: Film,
      color: "text-blue-400",
    },
    {
      label: "Cuentas",
      value: String(totalAccounts),
      icon: Users,
      color: "text-emerald-400",
    },
    {
      label: "Vistas",
      value: formatNumber(totalViews),
      icon: Eye,
      color: "text-amber-400",
    },
    {
      label: "Likes",
      value: formatNumber(totalLikes),
      icon: Heart,
      color: "text-red-400",
    },
    {
      label: "Disco",
      value: diskTotal > 0 ? `${formatBytes(diskFree * 1024 ** 3)} / ${formatBytes(diskTotal * 1024 ** 3)}` : formatBytes(diskFree * 1024 ** 3),
      sub: diskTotal > 0 ? `${Math.round((diskFree / diskTotal) * 100)}% libre` : undefined,
      icon: HardDrive,
      color: diskFree / diskTotal < 0.1 ? "text-red-400" : diskFree / diskTotal < 0.2 ? "text-amber-400" : "text-accent-400",
    },
  ];
}

export default function DashboardCards({ health, metrics }: DashboardCardsProps) {
  const cards = buildCards(health, metrics);

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-xl border border-gray-800 bg-gray-900 p-4"
        >
          <div className="flex items-center justify-between">
            <span className="text-gray-500 text-xs uppercase tracking-wider">
              {card.label}
            </span>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </div>
          <p className="mt-2 text-2xl font-bold text-gray-200">{card.value}</p>
          {card.sub && (
            <p className="text-gray-500 mt-0.5 text-xs">{card.sub}</p>
          )}
        </div>
      ))}
    </div>
  );
}
