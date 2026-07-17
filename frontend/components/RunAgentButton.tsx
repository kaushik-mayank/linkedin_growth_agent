"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { ProgressEvent, RunResult } from "@/lib/types";
import { Button, ErrorNote, Spinner } from "./ui";

// The 9 specialists in graph order. Some (copywriter/creative/critic) are skipped
// on a recovery week — that's expected, they just never light up.
const SPECIALISTS: { node: string; label: string }[] = [
  { node: "analyst", label: "Analyst" },
  { node: "profiler", label: "Audience Profiler" },
  { node: "researcher", label: "Researcher" },
  { node: "historian", label: "Historian" },
  { node: "strategist", label: "Strategist" },
  { node: "copywriter", label: "Copywriter" },
  { node: "creative_director", label: "Creative Director" },
  { node: "critic", label: "Critic" },
  { node: "librarian", label: "Librarian" },
];

export function RunAgentButton({
  projectId,
  onDone,
  disabled,
  label = "Generate this week's plan",
}: {
  projectId: string;
  onDone: (result: RunResult) => void;
  disabled?: boolean;
  label?: string;
}) {
  const [running, setRunning] = useState(false);
  const [currentLabel, setCurrentLabel] = useState<string>("");
  const [visited, setVisited] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setRunning(true);
    setError(null);
    setVisited(new Set());
    setCurrentLabel("Starting up…");

    try {
      const resp = await fetch(
        `${api.base}/projects/${projectId}/run-weekly/stream`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );

      if (!resp.ok || !resp.body) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body?.detail || `Server error (${resp.status})`);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          const line = part.split("\n").find((l) => l.startsWith("data: "));
          if (!line) continue;
          const event = JSON.parse(line.slice(6)) as ProgressEvent;

          if (event.type === "progress") {
            setCurrentLabel(event.label);
            setVisited((prev) => new Set(prev).add(event.node));
          } else if (event.type === "error") {
            throw new Error(event.message);
          } else if (event.type === "done") {
            setRunning(false);
            onDone(event.result);
            return;
          }
        }
      }
    } catch (e) {
      setError((e as Error).message);
      setRunning(false);
    }
  }

  if (!running) {
    return (
      <div>
        <Button onClick={run} variant="primary" disabled={disabled}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 3l14 9-14 9V3z" />
          </svg>
          {label}
        </Button>
        {error && (
          <div className="mt-3">
            <ErrorNote message={error} />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="flex items-center gap-2 text-sm font-medium">
        <Spinner className="text-brand" />
        <span>{currentLabel}</span>
      </div>
      <p className="mt-1 text-xs text-muted">
        This takes 15–90 seconds. The team is working through your data.
      </p>
      <div className="mt-4 space-y-1.5">
        {SPECIALISTS.map((s) => {
          const done = visited.has(s.node);
          const active = currentLabel.startsWith(s.label);
          return (
            <div
              key={s.node}
              className={`flex items-center gap-2.5 text-sm ${
                done || active ? "text-fg" : "text-muted/60"
              }`}
            >
              <span
                className={`flex h-4 w-4 items-center justify-center rounded-full border text-[10px] ${
                  done
                    ? "border-positive bg-positive text-white"
                    : active
                    ? "border-brand text-brand"
                    : "border-border"
                }`}
              >
                {done ? (
                  <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 6L9 17l-5-5" />
                  </svg>
                ) : active ? (
                  <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-brand" />
                ) : null}
              </span>
              {s.label}
            </div>
          );
        })}
      </div>
    </div>
  );
}
