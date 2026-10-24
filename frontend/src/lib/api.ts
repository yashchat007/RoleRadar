const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const body = JSON.parse(text) as { detail?: string | { msg?: string }[] };
      if (typeof body.detail === "string") throw new Error(body.detail);
      if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        throw new Error(body.detail[0].msg);
      }
    } catch (e) {
      if (e instanceof Error && e.message !== text) throw e;
    }
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export type JobWithMatch = {
  id: string;
  company_id: string;
  company_name?: string | null;
  title: string;
  location?: string | null;
  listing_url: string;
  apply_url: string;
  deadline_at?: string | null;
  posted_at?: string | null;
  score?: number | null;
  preference_score?: number | null;
  resume_match_available?: boolean;
  eligible?: boolean | null;
  top_reason?: string | null;
  role_family?: string | null;
  company_logo_url?: string | null;
  eligibility_label?: string | null;
  eligibility_detail?: string | null;
  location_display?: string | null;
  career_level_label?: string | null;
};

export type JobListResponse = {
  items: JobWithMatch[];
  meta: {
    total: number;
    matching_total?: number;
    page?: number;
    page_size?: number;
    total_pages?: number;
    visible_count?: number;
    hidden_ineligible_count?: number;
    sort_label?: string;
    sources_degraded?: string[];
    has_resume?: boolean;
  };
};

export type CompanyDiscoverCard = {
  status_label?: string;
  india_internship_count?: number;
  last_scan_at?: string | null;
  coverage_note?: string | null;
  last_scan_jobs_seen?: number | null;
  id: string;
  name: string;
  career_page_url: string;
  parser_status: string;
  is_enabled: boolean;
  last_scan_status?: string | null;
  active_job_count: number;
  source_state: string;
  company_logo_url?: string | null;
  priority_rank?: number | null;
};

export type ResumeStatus = {
  has_resume: boolean;
  resume_id?: string | null;
  filename?: string | null;
  uploaded_at?: string | null;
};

export type JobDetail = JobWithMatch & {
  remote_flag?: boolean | null;
  listing_status: string;
  description_sections?: Record<string, unknown> | null;
  last_seen_at: string;
  last_verified_at?: string | null;
  lifecycle_status?: string | null;
  requisition_id?: string | null;
};

export type MatchDetail = {
  job_id: string;
  score: number | null;
  preference_score?: number | null;
  resume_match_available?: boolean;
  eligible: boolean;
  role_family?: string | null;
  eligibility_reasons: string[];
  factors: { name: string; weight: number; score: number; evidence: string[] }[];
  requirements: { text: string; status: string; evidence?: string | null }[];
  gaps: { requirement: string; estimated_score_delta: number; status: string }[];
  top_reasons: string[];
  computed_at: string;
};

export type TodayResponse = {
  headline: string;
  attention: {
    job_id: string;
    title: string;
    company_name: string;
    score: number;
    top_reason?: string | null;
    deadline_at?: string | null;
  }[];
  tracker_counts: Record<string, number>;
  upcoming_deadlines: TodayResponse["attention"];
  changelog: { message: string; created_at: string }[];
  sources_degraded: string[];
};

export type Profile = {
  skills: unknown[];
  education: unknown[];
  experience: unknown[];
  projects: unknown[];
  preferences: Record<string, unknown>;
  updated_at?: string | null;
};

export type TrackerBoard = {
  items: {
    id: string;
    job_id: string;
    title: string;
    company_name: string;
    stage: string;
    score?: number | null;
    stage_entered_at: string;
    deadline_at?: string | null;
    notes?: string | null;
  }[];
  counts_by_stage: Record<string, number>;
};

export type DiscoveryStatus = {
  enabled_companies: number;
  pending_validation: number;
  scanning: boolean;
  last_aggregate_scan_at?: string | null;
};

export const api = {
  getToday: () => request<TodayResponse>("/today"),
  getDiscoveryStatus: () => request<DiscoveryStatus>("/discovery/status"),
  getJobs: (params?: {
    q?: string;
    hide_ineligible?: boolean;
    min_score?: number;
    company_id?: string;
    page?: number;
    page_size?: number;
    india_only?: boolean;
    internships_only?: boolean;
    sort?: string;
  }) => {
    const sp = new URLSearchParams();
    if (params?.q) sp.set("q", params.q);
    if (params?.hide_ineligible === false) sp.set("hide_ineligible", "false");
    if (params?.min_score != null) sp.set("min_score", String(params.min_score));
    if (params?.company_id) sp.set("company_id", params.company_id);
    if (params?.page != null) sp.set("page", String(params.page));
    if (params?.page_size != null) sp.set("page_size", String(params.page_size));
    if (params?.india_only === false) sp.set("india_only", "false");
    if (params?.internships_only === false) sp.set("internships_only", "false");
    if (params?.sort) sp.set("sort", params.sort);
    const qs = sp.toString();
    return request<JobListResponse>(`/jobs${qs ? `?${qs}` : ""}`);
  },
  getDiscoverCompanies: () => request<CompanyDiscoverCard[]>("/companies/discover"),
  getJob: (id: string) => request<JobDetail>(`/jobs/${id}`),
  getJobMatch: (id: string) => request<MatchDetail>(`/jobs/${id}/match`),
  getProfile: () => request<Profile>("/profile"),
  patchProfile: (body: Partial<Profile>) =>
    request<Profile>("/profile", { method: "PATCH", body: JSON.stringify(body) }),
  getResumeStatus: () => request<ResumeStatus>("/resume"),
  uploadResume: async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${BASE}/resume`, { method: "POST", body: fd });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  deleteResume: () => request<void>("/resume", { method: "DELETE" }),
  bookmark: (jobId: string) => request<{ bookmarked: boolean }>(`/saved/jobs/${jobId}`, { method: "POST" }),
  unbookmark: (jobId: string) =>
    request<{ bookmarked: boolean }>(`/saved/jobs/${jobId}`, { method: "DELETE" }),
  getSaved: () => request<JobWithMatch[]>("/saved"),
  getTracker: () => request<TrackerBoard>("/tracker"),
  patchTracker: (jobId: string, stage: string) =>
    request(`/tracker/${jobId}`, { method: "PATCH", body: JSON.stringify({ stage }) }),
  getSettings: () =>
    request<{ email: string; theme: string; email_digest_enabled: boolean }>("/settings"),
  patchSettings: (body: { theme?: string; email_digest_enabled?: boolean }) =>
    request<{ email: string; theme: string; email_digest_enabled: boolean }>("/settings", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  getWatches: () =>
    request<Watch[]>("/watches"),
  createWatch: (name: string, filters: Record<string, unknown>) =>
    request<Watch>("/watches", { method: "POST", body: JSON.stringify({ name, filters }) }),
  deleteWatch: (id: string) => request(`/watches/${id}`, { method: "DELETE" }),
  sendDigest: () =>
    request<{
      digest_sent: boolean;
      digest_status: string;
      digest_detail?: string | null;
      watch_emails: number;
      smtp_error?: string | null;
    }>("/digest/send", { method: "POST" }),
};

export type Watch = {
  id: string;
  name: string;
  filters: Record<string, unknown>;
  created_at: string;
  last_notified_at?: string | null;
};
