"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Week, Post } from "@/lib/types";
import {
  Badge,
  Button,
  Card,
  ErrorNote,
  SectionTitle,
  Skeleton,
} from "@/components/ui";
import { CadenceCard } from "@/components/CadenceCard";
import { AudiencePanel } from "@/components/AudiencePanel";
import { PostCard } from "@/components/PostCard";
import { DownloadPlanButton } from "@/components/DownloadPlanButton";

export default function WeekPage({
  params,
}: {
  params: { id: string; weekId: string };
}) {
  const { id, weekId } = params;
  const [week, setWeek] = useState<Week | null>(null);
  const [posts, setPosts] = useState<Post[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getWeek(id, weekId)
      .then(({ week, posts }) => {
        setWeek(week);
        setPosts(posts);
      })
      .catch((e: ApiError) => setError(e.message));
  }, [id, weekId]);

  if (error) {
    return (
      <div>
        <Button href={`/projects/${id}`} variant="ghost" className="mb-4 -ml-2">
          ← Back to dashboard
        </Button>
        <ErrorNote message={error} />
      </div>
    );
  }

  if (!week || !posts) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  const diagnosis = week.diagnosis?.analyst || null;
  const audience = week.diagnosis?.audience_profile || null;
  const research = week.research;
  const isRecovery = (week.cadence_decision?.posts_this_week ?? 0) === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Button href={`/projects/${id}`} variant="ghost" className="mb-3 -ml-2">
          ← Back to dashboard
        </Button>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wide text-muted">
            Week {week.week_number}
          </span>
        </div>
        <div className="mt-1 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">
            {week.theme || "Weekly plan"}
          </h1>
          <DownloadPlanButton week={week} posts={posts} />
        </div>
      </div>

      {/* Diagnosis */}
      {diagnosis && (
        <Card>
          <div className="flex flex-wrap items-center gap-2">
            <SectionTitle>Diagnosis</SectionTitle>
            <div className="mb-3 flex gap-2">
              <Badge tone="brand">{diagnosis.account_state}</Badge>
              {diagnosis.fatigue_detected && (
                <Badge tone="warn">audience fatigue</Badge>
              )}
            </div>
          </div>
          <p className="text-sm leading-relaxed">{diagnosis.narrative}</p>
          {diagnosis.fatigue_detected && diagnosis.fatigue_evidence && (
            <p className="mt-2 text-sm text-warn">
              {diagnosis.fatigue_evidence}
            </p>
          )}
          {diagnosis.unknowns && diagnosis.unknowns.length > 0 && (
            <div className="mt-4">
              <span className="text-xs font-medium uppercase tracking-wide text-muted">
                What we don't know yet
              </span>
              <ul className="mt-1.5 list-inside list-disc space-y-1 text-sm text-muted">
                {diagnosis.unknowns.map((u, i) => (
                  <li key={i}>{u}</li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}

      {/* Cadence */}
      {week.cadence_decision && (
        <CadenceCard cadence={week.cadence_decision} isRecovery={isRecovery} />
      )}

      {/* Live trends */}
      {research && research.findings && research.findings.length > 0 && (
        <Card>
          <SectionTitle>This week's live trends</SectionTitle>
          <div className="space-y-3">
            {research.findings.map((f, i) => (
              <a
                key={i}
                href={f.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-xl border border-border p-3 transition hover:border-brand/40"
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="text-sm font-medium text-brand">
                    {f.title}
                  </span>
                  {f.published_date && (
                    <span className="shrink-0 text-xs text-muted">
                      {f.published_date}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-sm text-muted">{f.why_relevant}</p>
              </a>
            ))}
          </div>
        </Card>
      )}

      {/* Recovery plan OR posts */}
      {isRecovery ? (
        <Card>
          <SectionTitle>Recovery / repositioning plan</SectionTitle>
          <p className="text-sm leading-relaxed">
            {week.reasoning ||
              "The agent recommended pausing posts this week to reset. No posts were generated."}
          </p>
        </Card>
      ) : (
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              {posts.length} {posts.length === 1 ? "post" : "posts"} this week
            </h2>
          </div>
          <div className="space-y-4">
            {posts.map((p) => (
              <PostCard key={p.id} post={p} />
            ))}
          </div>
        </div>
      )}

      {audience && <AudiencePanel profile={audience} />}
    </div>
  );
}
