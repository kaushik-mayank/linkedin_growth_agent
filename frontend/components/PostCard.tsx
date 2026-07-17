import type { Post } from "@/lib/types";
import { Badge } from "./ui";
import { CopyButton } from "./CopyButton";

const funnelTones: Record<string, "brand" | "positive" | "warn"> = {
  reach: "brand",
  trust: "positive",
  convert: "warn",
};

function scoreTone(score: number | null): "positive" | "warn" | "negative" {
  if (score == null) return "warn";
  if (score >= 8) return "positive";
  if (score >= 7) return "warn";
  return "negative";
}

export function PostCard({ post }: { post: Post }) {
  const hashtags = (post.hashtags || [])
    .map((h) => "#" + h.replace(/^#/, ""))
    .join(" ");

  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-surface-2 px-2 py-0.5 font-mono text-xs font-medium">
            {post.post_code}
          </span>
          {post.scheduled_day && (
            <Badge tone="neutral">
              {post.scheduled_day}
              {post.best_time ? ` · ${post.best_time}` : ""}
            </Badge>
          )}
          {post.format && <Badge tone="neutral">{post.format}</Badge>}
          {post.funnel_job && (
            <Badge tone={funnelTones[post.funnel_job] || "neutral"}>
              {post.funnel_job}
            </Badge>
          )}
        </div>
        {post.critic_score != null && (
          <Badge tone={scoreTone(post.critic_score)}>
            Critic {post.critic_score}/10
          </Badge>
        )}
      </div>

      {/* Hook */}
      <div className="mt-4">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wide text-muted">
            Hook
          </span>
          {post.hook && <CopyButton text={post.hook} />}
        </div>
        <p className="text-[15px] font-medium leading-snug">{post.hook}</p>
      </div>

      {/* Caption */}
      <div className="mt-4">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wide text-muted">
            Caption
          </span>
          {post.caption && (
            <CopyButton
              text={`${post.caption}${hashtags ? "\n\n" + hashtags : ""}`}
              label="Copy post"
            />
          )}
        </div>
        <div className="whitespace-pre-wrap rounded-xl border border-border bg-surface-2 p-4 text-sm leading-relaxed">
          {post.caption}
        </div>
      </div>

      {/* Meta grid */}
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        {hashtags && (
          <MetaBlock label="Hashtags">
            <span className="text-brand">{hashtags}</span>
          </MetaBlock>
        )}
        {post.tag_suggestions && (
          <MetaBlock label="Who to tag">{post.tag_suggestions}</MetaBlock>
        )}
        {post.image_prompt && post.image_prompt !== "text-only" && (
          <MetaBlock
            label="Image prompt"
            action={<CopyButton text={post.image_prompt} />}
          >
            {post.image_prompt}
          </MetaBlock>
        )}
        {post.psychology_notes && (
          <MetaBlock label="Why this works">{post.psychology_notes}</MetaBlock>
        )}
      </div>

      {post.critic_notes && (
        <p className="mt-4 border-t border-border pt-3 text-xs text-muted">
          <span className="font-medium">Editor's note:</span> {post.critic_notes}
        </p>
      )}
    </div>
  );
}

function MetaBlock({
  label,
  children,
  action,
}: {
  label: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border p-3">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-muted">
          {label}
        </span>
        {action}
      </div>
      <div className="text-sm leading-relaxed">{children}</div>
    </div>
  );
}
