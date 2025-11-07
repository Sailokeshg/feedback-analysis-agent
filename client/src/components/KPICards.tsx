import { useDashboardStore } from '../stores/dashboardStore';

const KPICard = ({
  title,
  value,
  subtitle,
  isLoading
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  isLoading?: boolean;
}) => {
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-1"></div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">{title}</h3>
      <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">{value}</div>
      {subtitle && <div className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</div>}
    </div>
  );
};

const KPICards = () => {
  const { dashboardSummary, isLoading } = useDashboardStore();

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      <KPICard
        title="Total Feedback"
        value={dashboardSummary?.total_feedback || 0}
        subtitle="All time"
        isLoading={isLoading}
      />
      <KPICard
        title="Negative Feedback"
        value={`${dashboardSummary?.negative_percentage?.toFixed(1) || 0}%`}
        subtitle="Of total feedback"
        isLoading={isLoading}
      />
      <KPICard
        title="Topics Identified"
        value={dashboardSummary?.topics_count || 0}
        subtitle="Unique topics"
        isLoading={isLoading}
      />
    </div>
  );
};

export default KPICards;
