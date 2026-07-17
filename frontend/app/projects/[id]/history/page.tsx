"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Week, Snapshot, Memory } from "@/lib/types";
import {
  Badge,
  Button,
  EmptyState,
  ErrorNote,
  SectionTitle,
  Skeleton,
} from "@/components/ui";

const memoryKinds: Record<
  string,
  { label: string; tone: "positive" | "negative" | "brand" | "warn" }
> = {
  winning_hook: { label: "What worked", tone: "positive" },
  flop: { label: "What flopped", tone: "negative" },
  audience_insight: { label: "Audience insight", tone: "brand" },
  strategy_shift: { label: "Strategy shift", tone: "warn" },
};

export default function HistoryPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const [weeks, setWeeks] = useState<Week[] | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[] | null>(null);
  const [memory, setMemory] = useState<Memory[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.listWeeks(id),
      api.listSnapshots(id),
      api.listMemory(id),
    ])
      .then(([w, s, m]) => {
        setWeeks(w);
        setSnapshots(s);
        setMemory(m);
      })
      .catch((e: ApiError) => setError(e.message));
  }, [id]);

  return (
    <div className="space-y-8">
      <div>
        <Button href={`/projects/${id}`} variant="ghost" className="mb-3 -ml-2">
          ← Back to dashboard
        </Button>
        <h1 className="text-2xl font-semibold">History & memory</h1>
        <p className="mt-1 text-sm text-muted">
          Every week the agent runs, and everything it has learned about this
          account.
        </p>
      </div>

      {error && <ErrorNote message={error} />}

      {/* What the agent has learned */}
      <section>
        <SectionTitle>What the agent has learned</SectionTitle>
        {!memory ? (
          <Skeleton className="h-24" />
        ) : memory.length === 0 ? (
          <p className="text-sm text-muted">
            Nothing yet. After the first run, the agent stores its most useful
            learnings here — and recalls them in future weeks.
          </p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {memory.map((m) => {
              const meta = m.kind ? memoryKinds[m.kind] : undefined;
              return (
                <div
                  key={m.id}
                  className="rounded-2xl border border-border bg-surface p-4"
                >
                  <Badge tone={meta?.tone || "neutral"}>
                    {meta?.label || m.kind || "note"}
                  </Badge>
                  <p className="mt-2 text-sm leading-relaxed">{m.content}</p>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Past weeks */}
      <section>
        <SectionTitle>Past weeks</SectionTitle>
        {!weeks ? (
          <Skeleton className="h-24" />
        ) : weeks.length === 0 ? (
          <EmptyState
            title="No weekly plans yet"
            description="Once you upload an export and run the agent, each week's plan will appear here."
            action={
              <Button href={`/projects/${id}`} variant="primary">
                Go to dashboard
              </Button>
            }
          />
        ) : (
          <div className="space-y-2">
            {weeks.map((w) => (
              <Link
                key={w.id}
                href={`/projects/${id}/weeks/${w.id}`}
                className="flex items-center justify-between rounded-xl border border-border bg-surface px-4 py-3 transition hover:border-brand/40"
              >
                <div className="flex items-center gap-3">
                  <span className="rounded-md bg-surface-2 px-2 py-0.5 text-xs font-medium">
                    W{w.week_number}
                  </span>
                  <span className="text-sm font-medium">
                    {w.theme || "Weekly plan"}
                  </span>
                  {(w.cadence_decision?.posts_this_week ?? 0) === 0 && (
                    <Badge tone="warn">recovery</Badge>
                  )}
                </div>
                <span className="text-sm text-muted">
                  {w.cadence_decision?.posts_this_week ?? 0} posts →
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Past uploads */}
      <section>
        <SectionTitle>Past uploads</SectionTitle>
        {!snapshots ? (
          <Skeleton className="h-24" />
        ) : snapshots.length === 0 ? (
          <p className="text-sm text-muted">No exports uploaded yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-border">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-muted">
                <tr>
                  <th className="px-4 py-2.5 text-left font-medium">Period</th>
                  <th className="px-4 py-2.5 text-right font-medium">Followers</th>
                  <th className="px-4 py-2.5 text-right font-medium">Impressions</th>
                  <th className="px-4 py-2.5 text-right font-medium">Posts</th>
                </tr>
              </thead>
              <tbody>
                {[...snapshots].reverse().map((s) => (
                  <tr key={s.id} className="border-t border-border">
                    <td className="px-4 py-2.5">
                      {s.period_start} → {s.period_end}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums">
                      {(s.followers_total ?? 0).toLocaleString()}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums">
                      {(s.impressions ?? 0).toLocaleString()}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums">
                      {s.posts_published ?? 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
