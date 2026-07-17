import { Sparkline } from "./Sparkline";

function formatNumber(n: number): string {
  if (Math.abs(n) >= 1000) return n.toLocaleString();
  return String(n);
}

export function StatCard({
  label,
  value,
  suffix = "",
  delta,
  history,
  higherIsBetter = true,
}: {
  label: string;
  value: number;
  suffix?: string;
  delta?: number | null;
  history: number[];
  higherIsBetter?: boolean;
}) {
  const hasDelta = delta !== undefined && delta !== null && delta !== 0;
  const positive = (delta ?? 0) > 0;
  const good = higherIsBetter ? positive : !positive;
  const tone = good ? "positive" : "negative";

  return (
    <div className="rounded-2xl border border-border bg-surface p-4">
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-muted">
          {label}
        </span>
        <Sparkline values={history} tone={hasDelta ? tone : "brand"} width={72} height={26} />
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-semibold tabular-nums">
          {formatNumber(value)}
          {suffix}
        </span>
        {hasDelta && (
          <span
            className={`inline-flex items-center gap-0.5 text-xs font-medium ${
              good ? "text-positive" : "text-negative"
            }`}
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ transform: positive ? "none" : "rotate(180deg)" }}>
              <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
            {formatNumber(Math.abs(delta as number))}
            {suffix}
          </span>
        )}
        {!hasDelta && (
          <span className="text-xs text-muted">no prior week</span>
        )}
      </div>
    </div>
  );
}
