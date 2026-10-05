export type Capability = "lead" | "admin" | "audit" | "approvals";
export interface Person {
  id: string;
  name: string;
  email: string;
  title: string;
  team: string;
  bio?: string;
}
export interface Session extends Person {
  capabilities: Capability[];
  teams: { id: string; name: string }[];
  led_teams: { id: string; name: string }[];
  organization: string;
}
export interface Project {
  id: string;
  name: string;
  description: string;
  code: string;
  color: string;
  status: string;
  members: Person[];
  steward: string;
}
export interface Update {
  is_blocked?: boolean;
  id: string;
  owner_id: string;
  owner_name: string;
  team_id: string;
  team_name: string;
  work_date: string;
  body: string;
  status: "draft" | "published" | "deletion_requested";
  visibility: "private" | "lead_visible";
  version: number;
  revisions: { version: number; body: string; date: string }[];
}
export interface Document {
  id: string;
  title: string;
  project_id: string;
  project_name: string;
  uploader_id: string;
  uploader_name: string;
  classification: "project" | "restricted";
  status:
    | "unpublished"
    | "processing"
    | "published"
    | "failed"
    | "quarantined"
    | "deletion_requested";
  version: number;
  type: string;
  size: string;
  updated_at: string;
  grants: string[];
  can_manage: boolean;
}
export interface Citation {
  id: string;
  title: string;
  source_type: "document" | "update" | "profile";
  source_id: string;
  version: number;
  locator: string;
}
export interface Message {
  id: string;
  question: string;
  answer?: string;
  state: "answered" | "insufficient" | "access_changed";
  citations: Citation[];
}
export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
}
export interface Audit {
  id: string;
  actor: string;
  action: string;
  target: string;
  decision: string;
  reason: string;
  policy_version: string;
  date: string;
}
export interface Approval {
  id: string;
  requester: string;
  scope: string;
  reason: string;
  status: string;
  can_review: boolean;
}
export interface List<T> {
  results: T[];
  next: string | null;
}
export interface SearchResult {
  id: string;
  title: string;
  snippet: string;
  type: "document" | "update" | "profile";
}

export type DashboardView = "employee" | "lead" | "admin" | "security";
export interface DashboardData {
  view: DashboardView;
  available_views: DashboardView[];
  date: string;
  event: string;
  cards: Record<string, number>;
  updates?: Update[];
  projects?: Project[];
  documents?: Document[];
  teams?: { id: string; name: string; count: number; updates: Update[] }[];
  blockers?: Update[];
  accounts?: { id: string; name: string; email: string; active: boolean }[];
  invitations?: { id: string; email: string; expires_at: string }[];
  approvals?: Approval[];
  events?: Audit[];
  changes?: Audit[];
  security_settings?: { name: string; value: string }[];
}
