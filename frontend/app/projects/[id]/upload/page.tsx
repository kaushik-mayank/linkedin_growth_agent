"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { ParsedExport } from "@/lib/types";
import { Button, Card, ErrorNote, SectionTitle, Spinner } from "@/components/ui";

type Preview = ParsedExport & { file_name: string };

function PreviewStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-border bg-surface-2 px-4 py-3">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold tabular-nums">{value}</div>
    </div>
  );
}

export default function UploadPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { id } = params;
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [dragging, setDragging] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(f: File) {
    setError(null);
    setPreview(null);
    if (!f.name.toLowerCase().endsWith(".xlsx")) {
      setError("Please choose the .xlsx file you downloaded from LinkedIn.");
      return;
    }
    setFile(f);
    setParsing(true);
    try {
      const p = await api.previewUpload(id, f);
      setPreview(p);
    } catch (e) {
      setError((e as ApiError).message);
    } finally {
      setParsing(false);
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  }

  async function confirm() {
    if (!file) return;
    setSaving(true);
    setError(null);
    try {
      await api.confirmUpload(id, file);
      router.push(`/projects/${id}`);
    } catch (e) {
      setError((e as ApiError).message);
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <Button href={`/projects/${id}`} variant="ghost" className="mb-3 -ml-2">
        ← Back to dashboard
      </Button>
      <h1 className="text-2xl font-semibold">Upload analytics export</h1>
      <p className="mt-1 text-sm text-muted">
        In LinkedIn, go to your analytics → Export, and choose the last 7 days.
        Drop that .xlsx file here.
      </p>

      <div className="mt-6 space-y-4">
        {error && <ErrorNote message={error} />}

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 text-center transition ${
            dragging
              ? "border-brand bg-brand/5"
              : "border-border bg-surface hover:border-brand/40"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-surface-2 text-muted">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
            </svg>
          </div>
          <p className="text-sm font-medium">
            {file ? file.name : "Drop your .xlsx here, or click to browse"}
          </p>
          <p className="mt-1 text-xs text-muted">
            Only the file stays on your machine until you confirm.
          </p>
        </div>

        {parsing && (
          <div className="flex items-center gap-2 text-sm text-muted">
            <Spinner /> Reading your export…
          </div>
        )}

        {preview && (
          <Card className="animate-fade-in-up">
            <SectionTitle>Here's what we found — confirm to save</SectionTitle>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <PreviewStat
                label="Period"
                value={
                  preview.period.start && preview.period.end
                    ? `${preview.period.start} → ${preview.period.end}`
                    : "not detected"
                }
              />
              <PreviewStat
                label="Followers"
                value={(preview.followers.total ?? 0).toLocaleString()}
              />
              <PreviewStat
                label="New followers"
                value={preview.followers.new_this_period ?? 0}
              />
              <PreviewStat
                label="Impressions"
                value={preview.totals.impressions.toLocaleString()}
              />
              <PreviewStat
                label="Posts published"
                value={preview.totals.posts_published}
              />
              <PreviewStat
                label="Demographic categories"
                value={Object.keys(preview.demographics).length}
              />
            </div>

            {preview.warnings.length > 0 && (
              <div className="mt-4 space-y-2">
                {preview.warnings.map((w, i) => (
                  <div
                    key={i}
                    className="rounded-xl border border-warn/30 bg-warn/10 px-4 py-2.5 text-sm text-warn"
                  >
                    {w}
                  </div>
                ))}
              </div>
            )}

            {!preview.period.start && (
              <div className="mt-4">
                <ErrorNote message="No date range was detected on the DISCOVERY sheet — this file can't be saved without a period. Double-check you exported the right file." />
              </div>
            )}

            <div className="mt-5 flex items-center gap-3">
              <Button
                onClick={confirm}
                variant="primary"
                disabled={saving || !preview.period.start}
              >
                {saving ? "Saving…" : "Confirm & save"}
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setPreview(null);
                  setFile(null);
                }}
              >
                Choose a different file
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
