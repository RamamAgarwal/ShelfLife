/** Shapes returned by the ShelfLife API. Keep in step with backend/app/models.py. */

export type Category =
  | "pricing"
  | "version_api"
  | "product_status"
  | "statistic"
  | "leadership_role"
  | "law_regulation"
  | "event_status"
  | "static";

export type Verdict =
  | "fresh"
  | "uncertain"
  | "stale"
  | "unverified"
  | "not_time_sensitive"
  | "error";

export type Stance = "supports" | "contradicts" | "irrelevant";

export type ClaimKind =
  | "fact"
  | "assumption"
  | "calculation"
  | "recommendation"
  | "api_usage"
  | "availability";

export interface Claim {
  id: string;
  text: string;
  span: [number, number] | null;
  category: Category;
  entities: string[];
  time_sensitive: boolean;
  search_queries: string[];
  kind: ClaimKind;
  depends_on: string[];
  formula: string | null;
  number: number | null;
  passport_id: string | null;
}

export interface CheckContext {
  country?: string | null;
  currency?: string | null;
  edition?: string | null;
  environment?: string | null;
}

export interface RecalcInput {
  claim_id: string;
  stated: number | null;
  current: number | null;
}

export interface Recalculation {
  formula: string;
  stated: number | null;
  recomputed: number | null;
  inputs: RecalcInput[];
}

export interface DecisionInfo {
  holds: "yes" | "no" | "unclear";
  reason: string;
  revised: string | null;
  judged_by: string | null;
}

export interface Guard {
  action: "show" | "show_with_warning" | "withhold";
  reason: string;
}

export interface Evidence {
  id: string;
  url: string;
  title: string;
  domain: string;
  snippet: string;
  published_date: string | null;
  authority: number;
  recency: number;
  weight: number;
  stance: Stance;
  quote: string | null;
  favicon: string | null;
  group: string | null;
  counted: boolean;
  extracted: boolean;
}

export interface ScoreBreakdown {
  supporting_weight: number;
  contradicting_weight: number;
  agreement: number | null;
  best_recency: number;
  half_life_days: number;
  independent_sources: number;
}

export type ChangeType =
  | "value_changed"
  | "superseded"
  | "deprecated"
  | "discontinued"
  | "renamed"
  | "unclear";

export interface ChangeInfo {
  change_type: ChangeType;
  old_value: string | null;
  new_value: string;
  as_of: string | null;
  source_url: string | null;
}

export interface LlmCallInfo {
  served_by: string | null;
  is_fallback: boolean;
  primary_model: string | null;
  cache_hit: boolean;
  cache_hit_type: string | null;
}

export interface ClaimResult {
  claim: Claim;
  verdict: Verdict;
  freshness_score: number | null;
  confidence: number;
  current_value: string | null;
  explanation: string;
  evidence: Evidence[];
  score_breakdown: ScoreBreakdown | null;
  llm: LlmCallInfo | null;
  recheck_by: string | null;
  change: ChangeInfo | null;
  affected_by: string[];
  recalculation: Recalculation | null;
  decision: DecisionInfo | null;
  context_note: string | null;
}

export interface FallbackEvent {
  stage: string;
  provider: string | null;
  model: string | null;
  primary_provider: string | null;
  primary_model: string | null;
}

export interface LlmStageMetrics {
  calls: number;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  cache_hits: number;
  latency_ms: number;
}

export interface SearchStageMetrics {
  searches: number;
  cached_searches: number;
  credits: number;
}

export interface Metrics {
  llm_calls: number;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  cache_hits: number;
  fallback_events: FallbackEvent[];
  tavily_credits: number;
  latency_ms: number;
  per_stage: Record<string, LlmStageMetrics | SearchStageMetrics>;
  unpriced_calls: number;
}

export interface Citation {
  number: number;
  url: string;
  title: string;
  domain: string;
  published_date: string | null;
}

export interface AnswerEdit {
  claim_id: string;
  kind: "replace" | "flag" | "note";
  start: number | null;
  end: number | null;
  before: string;
  after: string;
  citation: number | null;
}

export interface Rewrite {
  corrected_answer: string;
  edits: AnswerEdit[];
  citations: Citation[];
}

export interface CheckResult {
  id: string;
  answer: string;
  question: string | null;
  check_date: string;
  claims: ClaimResult[];
  answer_score: number | null;
  verdict_counts: Partial<Record<Verdict, number>>;
  corrected_answer: string | null;
  edits: AnswerEdit[];
  citations: Citation[];
  metrics: Metrics;
  recheck_by: string | null;
  checked_at: string | null;
  guard: Guard | null;
  context: CheckContext | null;
  profile_id: string | null;
  profile_version: number | null;
}

export interface TimelineEntry {
  check_id: string;
  checked_at: string;
  verdict: Verdict;
  score: number | null;
}

export interface CheckTimeline {
  checks: { id: string; checked_at: string; answer_score: number | null }[];
  claims: { claim_id: string; claim_text: string; entries: TimelineEntry[] }[];
}

export interface AffectedAnswer {
  check_id: string;
  checked_at: string;
  answer_excerpt: string;
  claim_text: string;
  verdict: Verdict;
}

export interface WatchItem {
  check_id: string;
  checked_at: string;
  question: string | null;
  answer_excerpt: string;
  claim_id: string;
  claim_text: string;
  verdict: Verdict;
  recheck_by: string;
  status: "overdue" | "due_soon";
}

export interface CheckRequest {
  answer: string;
  question?: string;
  deep?: boolean;
  use_cache?: boolean;
  context?: CheckContext | null;
  profile_id?: string | null;
}

export interface Budget {
  max_limit: number | null;
  current_usage: number;
  reset_duration: string | null;
}

export interface BudgetStatus {
  configured: boolean;
  name?: string | null;
  is_active?: boolean;
  budgets: Budget[];
}

export interface GeneratedAnswer {
  question: string;
  answer: string;
  model: string;
  is_fallback: boolean;
  cache_hit: boolean;
  cost_usd: number | null;
  latency_ms: number;
}

export interface ServiceHealth {
  ok: boolean;
  detail: string;
}

export interface Health {
  status: "ok" | "degraded";
  bifrost: ServiceHealth;
  tavily: ServiceHealth & { rate_limited?: boolean; credits_used?: number | null; credits_limit?: number | null };
  missing_settings: string[];
  demo_mode?: boolean;
}

export interface CheckFailure {
  code: string;
  message: string;
}

export type CheckStreamEvent =
  | { type: "claims_extracted"; data: { claims: Claim[] } }
  | { type: "claim_evidence"; data: { claim_id: string; sources: unknown[] } }
  | { type: "claim_scored"; data: ClaimResult }
  | { type: "metrics"; data: Metrics }
  | { type: "rewrite_ready"; data: Rewrite }
  | { type: "done"; data: CheckResult }
  | { type: "error"; data: CheckFailure };

// --- workspace pages ---------------------------------------------------------

export interface CheckSummary {
  id: string;
  checked_at: string;
  question: string | null;
  answer_excerpt: string;
  answer_score: number | null;
  verdict_counts: Partial<Record<Verdict, number>>;
  guard: Guard["action"] | null;
  profile_id: string | null;
}

export interface DriftAlert {
  profile_id: string;
  profile_name: string;
  context: CheckContext;
  checks: CheckSummary[];
}

export interface Dashboard {
  demo_mode: boolean;
  totals: {
    checks: number;
    claims_checked: number;
    verdicts: Partial<Record<Verdict, number>>;
    stale_rate: number | null;
  };
  by_category: Record<string, Partial<Record<Verdict, number>>>;
  daily: { date: string; checks: number; stale: number }[];
  recent: CheckSummary[];
  watchlist: WatchItem[];
  drift: DriftAlert[];
  alerts: { kind: string; check_id: string; text: string; answer_excerpt: string }[];
  usage: {
    llm_calls: number;
    tokens: number;
    cost_usd: number;
    unpriced_calls: number;
    cache_hits: number;
    fallbacks: number;
    tavily_credits: number;
    avg_latency_ms: number | null;
  };
}

export interface PassportEntry {
  check_id: string;
  checked_at: string;
  verdict: Verdict;
  score: number | null;
  current_value: string | null;
}

export interface Passport {
  id: string;
  text: string;
  category: Category;
  kind: ClaimKind;
  status: Verdict;
  score: number | null;
  current_value: string | null;
  first_checked: string;
  last_checked: string;
  recheck_by: string | null;
  sources: string[];
  authority: number | null;
  checks: number;
  answers: number;
  history?: PassportEntry[];
}

export interface CompareRow {
  app: string;
  claim: string;
  verdict: Verdict;
  score: number | null;
  current_value: string | null;
  quote: string | null;
  source_url: string | null;
}

export interface Comparison {
  id: string;
  created_at: string;
  question: string | null;
  conflicts: number;
  clusters: {
    topic: string;
    category: Category;
    conflict: boolean;
    current_value: string | null;
    entries: CompareRow[];
  }[];
  apps: { app: string; answer: string; claims: number; stale: number; fresh: number; other: number }[];
  metrics: Metrics;
}

export interface RegressionRun {
  id: string;
  test_id: string;
  ran_at: string;
  passed: boolean;
  check_id: string | null;
  answer: string;
  model: string;
  problems: string[];
}

export interface RegressionTest {
  id: string;
  name: string;
  question: string;
  model: string | null;
  must_include: string[];
  created_at: string;
  last_run: RegressionRun | null;
  recent: boolean[];
}

export interface Profile {
  id: string;
  name: string;
  context: CheckContext;
  version: number;
  updated_at: string;
  drifted_checks?: CheckSummary[];
}

export interface LinkResult {
  url: string;
  final_url: string;
  http_status: number | null;
  quote: string | null;
  status: "ok" | "changed" | "moved" | "gone" | "blocked" | "error";
  detail: string;
  claim_id: string | null;
  claim_text?: string | null;
  source: string;
}

export interface BatchStatus {
  id: string;
  finished: boolean;
  items: {
    index: number;
    status: "queued" | "running" | "done" | "failed";
    question: string | null;
    answer_excerpt: string;
    check_id?: string;
    verdict_counts?: Partial<Record<Verdict, number>>;
    answer_score?: number | null;
    error?: string;
  }[];
}

export interface DemoScenario {
  id: string;
  label: string;
  description: string;
  question: string;
  answer?: string;
  answers?: { app: string; answer: string }[];
  context?: CheckContext | null;
}

export interface SystemStatus {
  demo_mode: boolean;
  bifrost: ServiceHealth & { url?: string; virtual_key?: { ok: boolean; configured: boolean; detail: string } };
  tavily: ServiceHealth & { rate_limited?: boolean; credits_used?: number | null; credits_limit?: number | null };
  cache_plugin: { known: boolean; enabled?: boolean; detail: string };
  budget: BudgetStatus & { error?: string };
  missing_settings: string[];
  settings: {
    model_fast: string;
    model_strong: string;
    model_stale: string;
    fallbacks_fast: string[];
    fallbacks_strong: string[];
    providers: string[];
    use_tavily_extract: boolean;
    tavily_concurrency: number;
    search_cache_ttl_hours: number;
    alert_webhook: boolean;
  };
}

export interface EvaluationData {
  available: boolean;
  summary?: {
    answers: number;
    gold_claims: number;
    gold_counts: Partial<Record<string, number>>;
    extraction_recall: number | null;
    stale_strict: { precision: number | null; recall: number | null; f1: number | null };
    stale_lenient: { precision: number | null; recall: number | null; f1: number | null };
    false_alarm_rate: number | null;
    unverified_rate: number | null;
    static_handled: number | null;
    confusion: Record<string, Record<string, number>>;
    by_topic: Record<string, { claims: number; extraction_recall: number | null; precision: number | null; recall: number | null; f1: number | null }>;
    avg_latency_ms: number | null;
    avg_cost_usd: number | null;
  };
  meta?: { run_date: string; model_fast: string; model_strong: string; cache_hit_rate: number | null };
}
