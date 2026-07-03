interface ProgressBarProps {
  value: number;
  max: number;
  label?: string;
  showCount?: boolean;
  className?: string;
}

export default function ProgressBar({
  value,
  max,
  label,
  showCount = true,
  className = "",
}: ProgressBarProps) {
  const percent = max > 0 ? Math.min((value / max) * 100, 100) : 0;

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      {(label || showCount) && (
        <div className="flex items-center justify-between">
          {label && <span className="text-gray-400 text-xs">{label}</span>}
          {showCount && (
            <span className="text-gray-500 text-xs">
              {value}/{max}
            </span>
          )}
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-800">
        <div
          className="h-full rounded-full bg-accent-500 transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
