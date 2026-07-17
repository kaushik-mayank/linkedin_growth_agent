"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Project, Snapshot, Week, RunResult } from "@/lib/types";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorNote,
  SectionTitle,
  Skeleton,
} from "@/components/ui";
import { StatCard } from "@/components/StatCard";
import { CadenceCard } from "@/components/CadenceCard";
import { AudiencePanel } from "@/components/AudiencePanel";
import { RunAgentButton } from "@/components/RunAgentButton";

const accountTypeLabels: Record<string, string> = {
  individual: "Individual",
  creator: "Creator",
  consultant: "Consultant",
  company_page: "Company Page",
  community: "Community",
};

function delta(curr?: number | null, prev?: number | null): number | null {
  if (curr == null || prev == null) return null;
  return Math.round((curr - prev) * 100) / 100;
}

export default function DashboardPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { id } = params;
  const [project, setProject] = useState<Project | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[] | null>(null);
  const [weeks, setWeeks] = useState<Week[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    Promise.all([
      api.getProject(id),
      api.listSnapshots(id),
      api.listWeeks(id),
    ])
      .then(([p, s, w]) => {
        setProject(p);
        setSnapshots(s);
        setWeeks(w);
      })
      .catch((e: ApiError) => setError(e.message));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  function onRunDone(result: RunResult) {
    router.push(`/projects/${id}/weeks/${result.week.id}`);
  }

  if (error) {
    return (
      <div>
        <Button href="/" variant="ghost" className="mb-4 -ml-2">
          ← All projects
        </Button>
        <ErrorNote message={error} />
      </div>
    );
  }

  if (!project || !snapshots || !weeks) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 sm:grid-cols-3">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
        <Skeleton className="h-40" />
      </div>
    );
  }

  const latest = snapshots[snapshots.length - 1];
  const prev = snapshots.length >= 2 ? snapshots[snapshots.length - 2] : null;
  const latestWeek = weeks[0] || null;
  const audienceProfile = latestWeek?.diagnosis?.audience_profile || null;
  const cadence = latestWeek?.cadence_decision || project.current_cadence;

  const followersHist = snapshots.map((s) => s.followers_total ?? 0);
  const impressionsHist = snapshots.map((s) => s.impressions ?? 0);
  const engagementHist = snapshots.map((s) => s.engagement_rate ?? 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Button href="/" variant="ghost" className="mb-3 -ml-2">
          ← All projects
        </Button>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold">{project.name}</h1>
              <Badge tone="neutral">
                {accountTypeLabels[project.account_type] || project.account_type}
              </Badge>
              {project.growth_stage && (
                <Badge tone="brand">{project.growth_stage}</Badge>
              )}
            </div>
            {project.niche && (
              <p className="mt-1 text-sm text-muted">{project.niche}</p>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button href={`/projects/${id}/upload`} variant="secondary">
              Upload export
            </Button>
            <Button href={`/projects/${id}/history`} variant="ghost">
              History
            </Button>
          </div>
        </div>
      </div>

      {snapshots.length === 0 ? (
        <EmptyState
          title="No data yet"
          description="Upload your first LinkedIn analytics export (the .xlsx you download from LinkedIn) so the agent has something to diagnose."
          action={
            <Button href={`/projects/${id}/upload`} variant="primary">
              Upload your first export
            </Button>
          }
        />
      ) : (
        <>
          {/* Stats */}
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard
              label="Followers"
              value={latest.followers_total ?? 0}
              delta={delta(latest.followers_total, prev?.followers_total)}
              history={followersHist}
            />
            <StatCard
              label="Impressions"
              value={latest.impressions ?? 0}
              delta={delta(latest.impressions, prev?.impressions)}
              history={impressionsHist}
            />
            <StatCard
              label="Engagement rate"
              value={latest.engagement_rate ?? 0}
              suffix="%"
              delta={delta(latest.engagement_rate, prev?.engagement_rate)}
              history={engagementHist}
            />
          </div>

          {/* Cadence hero */}
          {cadence ? (
            <CadenceCard
              cadence={cadence}
              growthStage={project.growth_stage}
              isRecovery={cadence.posts_this_week === 0}
            />
          ) : (
            <Card>
              <SectionTitle>This week's plan</SectionTitle>
              <p className="text-sm text-muted">
                You've uploaded data but haven't generated a plan yet. Run the
                agent to get your cadence decision and posts.
              </p>
            </Card>
          )}

          {/* Run agent */}
          <Card>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="font-semibold">
                  {latestWeek ? "Generate a fresh plan" : "Generate your first plan"}
                </h3>
                <p className="mt-0.5 text-sm text-muted">
                  Runs all 9 specialists on your latest export
                  {latest.file_name ? ` (${latest.file_name})` : ""}.
                </p>
              </div>
              <RunAgentButton projectId={id} onDone={onRunDone} />
            </div>
          </Card>

          {/* Audience */}
          {audienceProfile && <AudiencePanel profile={audienceProfile} />}

          {/* Latest plan link */}
          {latestWeek && (
            <Link
              href={`/projects/${id}/weeks/${latestWeek.id}`}
              className="flex items-center justify-between rounded-2xl border border-border bg-surface p-5 transition hover:border-brand/40"
            >
              <div>
                <span className="text-xs font-medium uppercase tracking-wide text-muted">
                  Week {latestWeek.week_number}
                </span>
                <h3 className="mt-0.5 font-semibold">
                  {latestWeek.theme || "View full plan"}
                </h3>
              </div>
              <span className="text-brand">→</span>
            </Link>
          )}
        </>
      )}
    </div>
  );
}
