'use client';

interface ProgressBarProps {
  current: number;
  total: number;
  message?:  string;
}

export default function ProgressBar({ current, total, message }: ProgressBarProps) {
  const percentage = (current / total) * 100;
  
  return (
    <div className="w-full space-y-2">
      <div className="flex justify-between text-sm">
        <span>{message || `${current}/${total} scenes`}</span>
        <span>{percentage.toFixed(1)}%</span>
      </div>
      
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
        <div
          className="bg-blue-500 h-full rounded-full transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}