import type { AudienceProfile } from "@/lib/types";
import { Card, SectionTitle } from "./ui";

function Row({ label, items }: { label: string; items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="flex flex-col gap-1 border-b border-border py-2.5 last:border-0 sm:flex-row sm:items-start sm:justify-between">
      <span className="text-xs font-medium uppercase tracking-wide text-muted">
        {label}
      </span>
      <span className="text-sm sm:max-w-[60%] sm:text-right">
        {items.slice(0, 3).join(", ")}
      </span>
    </div>
  );
}

export function AudiencePanel({ profile }: { profile: AudienceProfile }) {
  return (
    <Card>
      <SectionTitle>Who's actually following</SectionTitle>

      {profile.drift_detected && profile.drift_explanation && (
        <div className="mb-4 rounded-xl border border-warn/30 bg-warn/10 px-4 py-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-warn">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <path d="M12 9v4M12 17h.01" />
            </svg>
            Audience drift
          </div>
          <p className="mt-1 text-sm text-fg/90">{profile.drift_explanation}</p>
        </div>
      )}

      <p className="mb-3 text-sm text-muted">{profile.actual_audience_summary}</p>

      <div>
        <Row label="Job titles" items={profile.top_job_titles} />
        <Row label="Seniority" items={profile.top_seniority} />
        <Row label="Industries" items={profile.top_industries} />
        <Row label="Locations" items={profile.top_locations} />
        <Row label="Company sizes" items={profile.top_company_sizes} />
      </div>
    </Card>
  );
}
