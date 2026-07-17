"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Project } from "@/lib/types";
import { Badge, Button, EmptyState, ErrorNote, Skeleton } from "@/components/ui";

const accountTypeLabels: Record<string, string> = {
  individual: "Individual",
  creator: "Creator",
  consultant: "Consultant",
  company_page: "Company Page",
  community: "Community",
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listProjects()
      .then(setProjects)
      .catch((e: ApiError) => setError(e.message));
  }, []);

  return (
    <div>
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Your accounts</h1>
          <p className="mt-1 text-sm text-muted">
            Each project is one LinkedIn account the agent manages.
          </p>
        </div>
        <Button href="/new" variant="primary">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New project
        </Button>
      </div>

      {error && <ErrorNote message={error} />}

      {!projects && !error && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      )}

      {projects && projects.length === 0 && (
        <EmptyState
          title="No projects yet"
          description="Create your first project to start. You'll tell the agent who this account is for, then upload your first LinkedIn analytics export."
          action={
            <Button href="/new" variant="primary">
              Create your first project
            </Button>
          }
        />
      )}

      {projects && projects.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="group rounded-2xl border border-border bg-surface p-5 transition hover:border-brand/40 hover:shadow-sm"
            >
              <div className="flex items-center justify-between">
                <Badge tone="neutral">
                  {accountTypeLabels[p.account_type] || p.account_type}
                </Badge>
                {p.growth_stage && (
                  <Badge tone="brand">{p.growth_stage}</Badge>
                )}
              </div>
              <h3 className="mt-3 text-lg font-semibold group-hover:text-brand">
                {p.name}
              </h3>
              {p.niche && (
                <p className="mt-1 line-clamp-2 text-sm text-muted">{p.niche}</p>
              )}
              {p.current_cadence && (
                <p className="mt-3 text-xs text-muted">
                  Current plan:{" "}
                  <span className="font-medium text-fg">
                    {p.current_cadence.posts_this_week} posts/week
                  </span>
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
