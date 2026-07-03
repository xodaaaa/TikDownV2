import DashboardCards from "./DashboardCards";
import MonitorPanel from "./MonitorPanel";
import ActivityFeed from "./ActivityFeed";
import { useSystemHealth, useAccountMetrics } from "@/services/queries";
import Skeleton from "@/components/Skeleton";

export default function DashboardPage() {
  const { data: health, isLoading: healthLoading } = useSystemHealth();
  const { data: metrics, isLoading: metricsLoading } = useAccountMetrics();

  if (healthLoading || metricsLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-20 rounded-xl" />
        <Skeleton className="h-80 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <DashboardCards health={health} metrics={metrics} />
      <MonitorPanel health={health} />
      <ActivityFeed />
    </div>
  );
}
