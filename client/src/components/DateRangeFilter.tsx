import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useDashboardStore } from '../stores/dashboardStore';
import { DateRange } from '../types';

const DateRangeFilter = () => {
  const { dateRange, setDateRange } = useDashboardStore();
  const [searchParams, setSearchParams] = useSearchParams();

  const [localDateRange, setLocalDateRange] = useState<DateRange>({
    start: dateRange.start,
    end: dateRange.end,
  });

  // Sync URL params to local state on mount and URL changes
  useEffect(() => {
    const startParam = searchParams.get('start');
    const endParam = searchParams.get('end');

    if (startParam && endParam) {
      const start = new Date(startParam);
      const end = new Date(endParam);

      if (!isNaN(start.getTime()) && !isNaN(end.getTime())) {
        const newRange = { start, end };
        setLocalDateRange(newRange);
        setDateRange(newRange);
      }
    }
  }, [searchParams, setDateRange]);

  const handleDateChange = (type: 'start' | 'end', value: string) => {
    const date = new Date(value);
    if (isNaN(date.getTime())) return;

    const newRange = {
      ...localDateRange,
      [type]: date,
    };

    setLocalDateRange(newRange);

    // Update URL params
    const params = new URLSearchParams(searchParams);
    params.set('start', newRange.start.toISOString().split('T')[0]);
    params.set('end', newRange.end.toISOString().split('T')[0]);
    setSearchParams(params);

    // Update store
    setDateRange(newRange);
  };

  const formatDateForInput = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Date Range</h3>

      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
        <div className="flex-1 min-w-0">
          <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Start Date
          </label>
          <input
            id="start-date"
            type="date"
            value={formatDateForInput(localDateRange.start)}
            onChange={(e) => handleDateChange('start', e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100 sm:text-sm"
          />
        </div>

        <div className="flex-1 min-w-0">
          <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            End Date
          </label>
          <input
            id="end-date"
            type="date"
            value={formatDateForInput(localDateRange.end)}
            onChange={(e) => handleDateChange('end', e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100 sm:text-sm"
          />
        </div>

        <div className="flex items-end">
          <button
            onClick={() => {
              const today = new Date();
              const twoWeeksAgo = new Date(today.getTime() - 14 * 24 * 60 * 60 * 1000);
              handleDateChange('start', twoWeeksAgo.toISOString().split('T')[0]);
              setTimeout(() => {
                handleDateChange('end', today.toISOString().split('T')[0]);
              }, 0);
            }}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          >
            Reset to 14 days
          </button>
        </div>
      </div>
    </div>
  );
};

export default DateRangeFilter;
