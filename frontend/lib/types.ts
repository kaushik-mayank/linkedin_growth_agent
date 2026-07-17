// TypeScript shapes mirroring the FastAPI backend responses.

export type AccountType =
  | "individual"
  | "creator"
  | "consultant"
  | "company_page"
  | "community";

export interface Project {
  id: string;
  name: string;
  account_type: string;
  niche: string | null;
  audience: string | null;
  goal: string | null;
  notes: string | null;
  strategy: Strategy | null;
  growth_stage: string | null;
  current_cadence: CadenceDecision | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Snapshot {
  id: string;
  project_id: string;
  period_start: string;
  period_end: string;
  followers_total: number | null;
  followers_new: number | null;
  impressions: number | null;
  engagements: number | null;
  engagement_rate: number | null;
  posts_published: number | null;
  raw: ParsedExport | null;
  file_name: string | null;
  created_at: string | null;
}

export interface ParsedExport {
  period: { start: string | null; end: string | null };
  discovery: Record<string, number>;
  daily: { date: string; impressions: number; engagements: number }[];
  top_posts: {
    url: string;
    published?: string | null;
    engagements?: number;
    impressions?: number;
  }[];
  followers: {
    total?: number;
    daily?: { date: string; new_followers: number }[];
    new_this_period?: number;
  };
  demographics: Record<string, { value: string; percentage: number }[]>;
  warnings: string[];
  totals: {
    impressions: number;
    engagements: number;
    engagement_rate: number;
    posts_published: number;
  };
}

export interface CadenceDecision {
  posts_this_week: number;
  schedule: { day: string; reason: string }[];
  reasoning: string;
}

export interface Strategy {
  growth_stage: string;
  week_theme: string;
  cadence_decision: CadenceDecision;
  funnel_mix: { reach_pct: number; trust_pct: number; convert_pct: number };
  positioning_shift: string | null;
  reasoning_summary: string;
  is_recovery_week: boolean;
  recovery_plan: string | null;
}

export interface AnalystDiagnosis {
  account_state: string;
  fatigue_detected: boolean;
  fatigue_evidence: string | null;
  key_observations: string[];
  unknowns: string[];
  narrative: string;
}

export interface AudienceProfile {
  top_job_titles: string[];
  top_seniority: string[];
  top_industries: string[];
  top_locations: string[];
  top_company_sizes: string[];
  actual_audience_summary: string;
  drift_detected: boolean;
  drift_explanation: string | null;
  recommendation: string;
}

export interface ResearchFinding {
  title: string;
  url: string;
  published_date: string | null;
  why_relevant: string;
}

export interface ResearchFindings {
  findings: ResearchFinding[];
  no_useful_trends: boolean;
  note: string | null;
}

export interface Week {
  id: string;
  project_id: string;
  week_number: number;
  snapshot_id: string | null;
  theme: string | null;
  diagnosis: {
    analyst: AnalystDiagnosis | null;
    audience_profile: AudienceProfile | null;
  } | null;
  cadence_decision: CadenceDecision | null;
  research: ResearchFindings | null;
  reasoning: string | null;
  created_at: string | null;
}

export interface Post {
  id: string;
  project_id: string;
  week_id: string;
  post_code: string | null;
  scheduled_day: string | null;
  best_time: string | null;
  format: string | null;
  funnel_job: string | null;
  hook: string | null;
  caption: string | null;
  hashtags: string[] | null;
  tag_suggestions: string | null;
  image_prompt: string | null;
  psychology_notes: string | null;
  critic_score: number | null;
  critic_notes: string | null;
  created_at: string | null;
}

export interface Memory {
  id: string;
  project_id: string | null;
  kind: string | null;
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string | null;
}

export interface RunResult {
  week: Week;
  posts: Post[];
  plan_filename: string;
  is_recovery_week: boolean;
  warnings: string[];
}

export type ProgressEvent =
  | { type: "progress"; node: string; label: string }
  | { type: "done"; result: RunResult }
  | { type: "error"; message: string };
