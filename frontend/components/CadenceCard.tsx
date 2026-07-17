import type { CadenceDecision } from "@/lib/types";
import { Badge } from "./ui";

export function CadenceCard({
  cadence,
  growthStage,
  isRecovery,
}: {
  cadence: CadenceDecision;
  growthStage?: string | null;
  isRecovery?: boolean;
}) {
  const count = cadence.posts_this_week;

  return (
    <div className="relative overflow-hidden rounded-2xl border border-brand/30 bg-gradient-to-br from-brand/10 to-transparent p-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-brand">
          The agent's decision this week
        </span>
        {growthStage && <Badge tone="brand">{growthStage} stage</Badge>}
        {isRecovery && <Badge tone="warn">recovery week</Badge>}
      </div>

      <div className="mt-3 flex items-baseline gap-3">
        <span className="text-5xl font-bold tabular-nums">{count}</span>
        <span className="text-lg text-muted">
          {count === 0
            ? "posts — pause and reposition"
            : count === 1
            ? "post this week"
            : "posts this week"}
        </span>
      </div>

      <p className="mt-4 text-sm leading-relaxed text-fg/90">
        {cadence.reasoning}
      </p>

      {cadence.schedule && cadence.schedule.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {cadence.schedule.map((s, i) => (
            <div
              key={i}
              className="rounded-lg border border-border bg-surface px-3 py-1.5 text-xs"
              title={s.reason}
            >
              <span className="font-medium">{s.day}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
