"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { Button, Card, ErrorNote } from "@/components/ui";

const accountTypes = [
  { value: "individual", label: "Individual professional" },
  { value: "creator", label: "Creator" },
  { value: "consultant", label: "Consultant" },
  { value: "company_page", label: "Company page" },
  { value: "community", label: "Community" },
];

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium">{label}</span>
      {hint && <span className="ml-2 text-xs text-muted">{hint}</span>}
      <div className="mt-1.5">{children}</div>
    </label>
  );
}

const inputCls =
  "w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20";

export default function NewProjectPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    account_type: "individual",
    niche: "",
    audience: "",
    goal: "",
    notes: "",
  });

  function update(key: keyof typeof form, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!form.name.trim()) {
      setError("Please give your project a name.");
      return;
    }
    setSaving(true);
    try {
      const project = await api.createProject({
        name: form.name.trim(),
        account_type: form.account_type,
        niche: form.niche.trim() || null,
        audience: form.audience.trim() || null,
        goal: form.goal.trim() || null,
        notes: form.notes.trim() || null,
      });
      router.push(`/projects/${project.id}`);
    } catch (e) {
      setError((e as ApiError).message);
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6">
        <Button href="/" variant="ghost" className="mb-3 -ml-2">
          ← All projects
        </Button>
        <h1 className="text-2xl font-semibold">New project</h1>
        <p className="mt-1 text-sm text-muted">
          Tell the agent who this account is for. The more specific you are, the
          sharper its strategy.
        </p>
      </div>

      <Card>
        <form onSubmit={submit} className="space-y-5">
          {error && <ErrorNote message={error} />}

          <Field label="Project name">
            <input
              className={inputCls}
              value={form.name}
              onChange={(e) => update("name", e.target.value)}
              placeholder="e.g. Jane's personal brand"
              autoFocus
            />
          </Field>

          <Field label="Account type">
            <select
              className={inputCls}
              value={form.account_type}
              onChange={(e) => update("account_type", e.target.value)}
            >
              {accountTypes.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Niche" hint="what this account is about">
            <input
              className={inputCls}
              value={form.niche}
              onChange={(e) => update("niche", e.target.value)}
              placeholder="e.g. B2B SaaS growth marketing"
            />
          </Field>

          <Field label="Target audience" hint="who you want to reach">
            <input
              className={inputCls}
              value={form.audience}
              onChange={(e) => update("audience", e.target.value)}
              placeholder="e.g. Heads of Marketing at Series A–C startups"
            />
          </Field>

          <Field label="Goal">
            <input
              className={inputCls}
              value={form.goal}
              onChange={(e) => update("goal", e.target.value)}
              placeholder="e.g. Build authority and generate inbound leads"
            />
          </Field>

          <Field label="Notes" hint="anything else the agent should know">
            <textarea
              className={`${inputCls} min-h-[90px] resize-y`}
              value={form.notes}
              onChange={(e) => update("notes", e.target.value)}
              placeholder="e.g. I can share real client stories; I post in IST; I dislike hustle-culture tone."
            />
          </Field>

          <div className="flex items-center gap-3 pt-2">
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? "Creating…" : "Create project"}
            </Button>
            <Button href="/" variant="ghost">
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
