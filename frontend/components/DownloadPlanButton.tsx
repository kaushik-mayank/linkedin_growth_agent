"use client";

import type { Week, Post } from "@/lib/types";
import { Button } from "./ui";

function buildMarkdown(week: Week, posts: Post[]): string {
  const d = week.diagnosis?.analyst;
  const cadence = week.cadence_decision;
  const research = week.research;
  const isRecovery = (cadence?.posts_this_week ?? 0) === 0;
  const lines: string[] = [];

  lines.push(`# Week ${week.week_number} — ${week.theme || "Plan"}`);
  lines.push("");
  if (d) {
    lines.push("## Diagnosis");
    lines.push(`**Account state:** ${d.account_state}`);
    lines.push("");
    lines.push(d.narrative || "");
    lines.push("");
  }
  if (cadence) {
    lines.push("## Cadence decision");
    lines.push(`**Posts this week: ${cadence.posts_this_week}**`);
    lines.push("");
    lines.push(cadence.reasoning || "");
    lines.push("");
  }
  if (research?.findings?.length) {
    lines.push("## This week's live trends");
    for (const f of research.findings) {
      lines.push(`- [${f.title}](${f.url}) — ${f.why_relevant}`);
    }
    lines.push("");
  }
  if (isRecovery) {
    lines.push("## Recovery / repositioning plan");
    lines.push(week.reasoning || "");
    lines.push("");
  } else {
    lines.push("## Posts");
    for (const p of posts) {
      lines.push(
        `### ${p.post_code} — ${p.scheduled_day || ""} ${p.best_time || ""}`
      );
      lines.push(
        `**Format:** ${p.format} | **Funnel:** ${p.funnel_job} | **Critic:** ${p.critic_score}/10`
      );
      lines.push("");
      lines.push(`**Hook:** ${p.hook}`);
      lines.push("");
      lines.push("**Caption:**");
      lines.push("```");
      lines.push(p.caption || "");
      lines.push("```");
      lines.push("");
      const tags = (p.hashtags || []).map((h) => "#" + h.replace(/^#/, "")).join(" ");
      if (tags) lines.push(`**Hashtags:** ${tags}`);
      if (p.tag_suggestions) lines.push(`**Tag:** ${p.tag_suggestions}`);
      if (p.image_prompt && p.image_prompt !== "text-only")
        lines.push(`**Image prompt:** ${p.image_prompt}`);
      if (p.psychology_notes) lines.push(`**Why it works:** ${p.psychology_notes}`);
      lines.push("");
    }
  }
  return lines.join("\n");
}

export function DownloadPlanButton({
  week,
  posts,
}: {
  week: Week;
  posts: Post[];
}) {
  function download() {
    const md = buildMarkdown(week, posts);
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const stamp = new Date().toISOString().slice(0, 10);
    a.href = url;
    a.download = `plan_week${String(week.week_number).padStart(2, "0")}_${stamp}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Button onClick={download} variant="secondary">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
      </svg>
      Download plan
    </Button>
  );
}
