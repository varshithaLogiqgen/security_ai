// Synthetic, memory-only interaction model. Never used as an authorization boundary.
import type {
  Session,
  Person,
  Project,
  Update,
  Document,
  Conversation,
  Audit,
  Approval,
  SearchResult,
  List,
} from "../../types";
import { ApiError } from "./client";
const asha: Person = {
  id: "asha",
  name: "Asha Rao",
  email: "asha@example.test",
  title: "Product engineer",
  team: "Payments",
  bio: "Building thoughtful, reliable payment experiences.",
};
const dev: Person = {
  id: "dev",
  name: "Dev Shah",
  email: "dev@example.test",
  title: "Platform engineer",
  team: "Platform",
};
const meera: Person = {
  id: "meera",
  name: "Meera Iyer",
  email: "meera@example.test",
  title: "Engineering lead",
  team: "Payments",
};
const ravi: Person = {
  id: "ravi",
  name: "Ravi Kumar",
  email: "ravi@example.test",
  title: "Software engineer",
  team: "Payments",
};
export const demoSession: Session = {
  ...asha,
  organization: "Northstar",
  capabilities: [],
  teams: [{ id: "payments", name: "Payments" }],
  led_teams: [],
};
const people = [asha, dev, meera, ravi];
const projects: Project[] = [
  {
    id: "atlas",
    name: "Atlas",
    code: "AT",
    description:
      "A reliable foundation for the next generation of payments. Shared knowledge, architecture, and delivery.",
    color: "blue",
    status: "Active",
    members: [asha, dev],
    steward: "Meera Iyer",
  },
];
let updates: Update[] = [
  {
    id: "u1",
    owner_id: "asha",
    owner_name: "Asha Rao",
    team_id: "payments",
    team_name: "Payments",
    work_date: "2026-10-04",
    body: "Completed the payment retry flow and documented the edge cases. Next up: integration testing with the platform team.",
    status: "published",
    visibility: "lead_visible",
    version: 1,
    revisions: [],
  },
  {
    id: "u2",
    owner_id: "asha",
    owner_name: "Asha Rao",
    team_id: "payments",
    team_name: "Payments",
    work_date: "2026-10-03",
    body: "Exploring a simpler approach to reconciliation. Collected notes and questions for the next design discussion.",
    status: "draft",
    visibility: "private",
    version: 1,
    revisions: [],
  },
  {
    id: "u3",
    owner_id: "asha",
    owner_name: "Asha Rao",
    team_id: "payments",
    team_name: "Payments",
    work_date: "2026-10-02",
    body: "Updated the Atlas onboarding guide and paired with Dev on the service boundaries.",
    status: "published",
    visibility: "lead_visible",
    version: 1,
    revisions: [],
  },
];
let documents: Document[] = [
  {
    id: "d1",
    title: "Atlas · Project overview",
    project_id: "atlas",
    project_name: "Atlas",
    uploader_id: "asha",
    uploader_name: "Asha Rao",
    classification: "project",
    status: "published",
    version: 2,
    type: "PDF",
    size: "240 KB",
    updated_at: "2026-10-04",
    grants: [],
    can_manage: true,
  },
  {
    id: "d2",
    title: "Payment service architecture",
    project_id: "atlas",
    project_name: "Atlas",
    uploader_id: "dev",
    uploader_name: "Dev Shah",
    classification: "project",
    status: "published",
    version: 1,
    type: "PDF",
    size: "1.2 MB",
    updated_at: "2026-10-03",
    grants: [],
    can_manage: false,
  },
  {
    id: "d3",
    title: "Integration checklist",
    project_id: "atlas",
    project_name: "Atlas",
    uploader_id: "asha",
    uploader_name: "Asha Rao",
    classification: "restricted",
    status: "published",
    version: 1,
    type: "TXT",
    size: "4 KB",
    updated_at: "2026-10-02",
    grants: ["asha"],
    can_manage: true,
  },
];
const conversations: Conversation[] = [];
const approvals: Approval[] = [];
const audits: Audit[] = [];
let personal = { phone: "", address: "", emergency_contact: "" };
const uploaded = new Map<string, File>();
const list = <T>(results: T[]): List<T> => ({ results, next: null });
const clone = <T>(value: T): T => structuredClone(value);
const missing = () => {
  throw new ApiError(
    404,
    "This page is unavailable or you no longer have access.",
  );
};
const id = () => crypto.randomUUID();
export function demoDownload(documentId: string) {
  const doc = documents.find((d) => d.id === documentId);
  if (!doc || doc.status !== "published") return missing();
  return (
    uploaded.get(documentId) ||
    new Blob(
      [
        `SYNTHETIC DEMO FILE\n${doc.title}\nAtlas brings together the payment platform foundation. The next milestone is integration testing.`,
      ],
      { type: "text/plain" },
    )
  );
}
export async function demoRequest<T>(
  path: string,
  method = "GET",
  payload?: unknown,
): Promise<T> {
  await new Promise((resolve) => setTimeout(resolve, 180));
  const [pathname, query] = path.split("?");
  const parts = pathname.split("/").filter(Boolean);
  const body = (payload || {}) as Record<string, any>;
  let result: unknown;
  if (pathname === "/me") result = demoSession;
  else if (pathname === "/auth/logout") result = undefined;
  else if (pathname === "/projects") result = list(projects);
  else if (parts[0] === "projects") {
    const project = projects.find((p) => p.id === parts[1]);
    if (!project) return missing();
    result =
      parts[2] === "documents"
        ? list(documents.filter((d) => d.project_id === project.id))
        : project;
  } else if (pathname === "/profiles") result = list(people);
  else if (parts[0] === "profiles") {
    const person = people.find((p) => p.id === parts[1]);
    if (!person) return missing();
    if (parts[2] === "personal") {
      if (person.id !== "asha") return missing();
      if (method === "PATCH") personal = { ...personal, ...body };
      result = personal;
    } else {
      if (method === "PATCH") {
        if (person.id !== "asha") return missing();
        person.bio = String(body.bio || "");
        demoSession.bio = person.bio;
      }
      result = person;
    }
  } else if (parts[0] === "updates") {
    if (parts.length === 1) {
      if (method === "POST") {
        const update: Update = {
          id: id(),
          owner_id: "asha",
          owner_name: asha.name,
          team_id: "payments",
          team_name: "Payments",
          work_date: String(body.work_date),
          body: String(body.body),
          status: "draft",
          visibility: "private",
          version: 1,
          revisions: [],
        };
        updates.unshift(update);
        result = update;
      } else result = list(updates);
    } else {
      const update = updates.find((u) => u.id === parts[1]);
      if (!update) return missing();
      if (
        method !== "GET" &&
        body.version !== undefined &&
        body.version !== update.version
      )
        throw new ApiError(
          409,
          "This item changed. Reload the page before saving again.",
        );
      if (method === "DELETE") {
        if (update.status !== "draft") return missing();
        updates = updates.filter((u) => u.id !== update.id);
      } else if (method === "PATCH") {
        if (update.status === "published")
          update.revisions.unshift({
            version: update.version,
            body: update.body,
            date: new Date().toISOString(),
          });
        Object.assign(update, {
          body: body.body ?? update.body,
          visibility: body.visibility ?? update.visibility,
          work_date: body.work_date ?? update.work_date,
        });
        update.version++;
      } else if (parts[2] === "publish") {
        update.status = "published";
        update.visibility = body.visibility;
        update.version++;
      } else if (parts[2] === "request-deletion")
        update.status = "deletion_requested";
      result = update;
    }
  } else if (parts[0] === "teams") return missing();
  else if (parts[0] === "documents") {
    if (parts.length === 1) {
      if (method === "POST") {
        const form = payload as FormData;
        const file = form.get("file") as File;
        if (
          !file ||
          !["pdf", "docx", "txt"].includes(
            file.name.split(".").pop()!.toLowerCase(),
          ) ||
          file.size > 10 * 1024 * 1024
        )
          throw new ApiError(
            400,
            "Choose a PDF, DOCX, or TXT file up to 10 MB.",
          );
        const doc: Document = {
          id: id(),
          title: String(form.get("title")),
          project_id: "atlas",
          project_name: "Atlas",
          uploader_id: "asha",
          uploader_name: asha.name,
          classification: "restricted",
          status: "unpublished",
          version: 1,
          type: file.name.split(".").pop()!.toUpperCase(),
          size: `${Math.max(1, Math.round(file.size / 1024))} KB`,
          updated_at: new Date().toISOString().slice(0, 10),
          grants: ["asha"],
          can_manage: true,
        };
        documents.unshift(doc);
        uploaded.set(doc.id, file);
        result = doc;
      } else result = list(documents);
    } else {
      const doc = documents.find((d) => d.id === parts[1]);
      if (!doc) return missing();
      if (method !== "GET" && !doc.can_manage) return missing();
      if (body.version !== undefined && body.version !== doc.version)
        throw new ApiError(
          409,
          "This item changed. Reload the page before saving again.",
        );
      if (parts[2] === "publish") {
        doc.classification = body.classification;
        doc.grants = body.grants;
        doc.status = "published";
        doc.version++;
      } else if (parts[2] === "access" && method === "PATCH") {
        if (
          doc.classification === "restricted" &&
          body.classification === "project" &&
          doc.status === "published"
        ) {
          const approval = {
            id: id(),
            requester: asha.name,
            scope: doc.id,
            reason: "Widen document access to current project members",
            status: "Pending steward approval",
            can_review: false,
          };
          approvals.push(approval);
          result = approval;
          return clone(result) as T;
        }
        doc.classification = body.classification;
        doc.grants = body.grants;
        doc.status = "unpublished";
        doc.version++;
      } else if (parts[2] === "request-deletion")
        doc.status = "deletion_requested";
      else if (parts[2] === "versions" && method === "POST") {
        const file = (payload as FormData).get("file") as File;
        uploaded.set(doc.id, file);
        doc.status = "unpublished";
        doc.version++;
        doc.type = file.name.split(".").pop()!.toUpperCase();
      }
      result = doc;
    }
  } else if (pathname === "/search") {
    const q = String(body.query || "").toLowerCase();
    const results: SearchResult[] = [
      ...documents
        .filter((d) => d.status === "published")
        .map((d) => ({
          id: d.id,
          title: d.title,
          snippet: `${d.project_name} · Version ${d.version}`,
          type: "document" as const,
        })),
      ...updates.map((u) => ({
        id: u.id,
        title: `${u.team_name} · ${u.work_date}`,
        snippet: u.body,
        type: "update" as const,
      })),
      ...people.map((p) => ({
        id: p.id,
        title: p.name,
        snippet: `${p.title} · ${p.team}`,
        type: "profile" as const,
      })),
    ];
    result = list(
      results.filter((r) =>
        `${r.title} ${r.snippet}`.toLowerCase().includes(q),
      ),
    );
  } else if (parts[0] === "conversations") {
    if (parts.length === 1) {
      if (method === "POST") {
        const conversation = {
          id: id(),
          title: "New conversation",
          messages: [],
        };
        conversations.unshift(conversation);
        result = conversation;
      } else result = list(conversations.map((c) => ({ ...c, messages: [] })));
    } else {
      const conversation = conversations.find((c) => c.id === parts[1]);
      if (!conversation) return missing();
      if (method === "DELETE") {
        conversations.splice(conversations.indexOf(conversation), 1);
        result = undefined;
      } else if (method === "POST" && parts[2] === "messages") {
        const question = String(body.question);
        const doc = documents.find(
          (d) => d.id === "d1" && d.status === "published",
        );
        const sufficient = /atlas|project|payment/i.test(question) && doc;
        const message = {
          id: id(),
          question,
          answer: sufficient
            ? "Atlas is building the foundation for the next generation of payments. The current focus is the payment retry flow, service boundaries, and integration testing.\n\nThis is a fixed synthetic example, not a live AI response."
            : "I couldn’t find enough information in your accessible sources to answer that question.",
          state: sufficient ? ("answered" as const) : ("insufficient" as const),
          citations: sufficient
            ? [
                {
                  id: id(),
                  title: doc.title,
                  source_type: "document" as const,
                  source_id: doc.id,
                  version: doc.version,
                  locator: "Project overview",
                },
              ]
            : [],
        };
        conversation.messages.push(message);
        conversation.title = question.slice(0, 60);
        result = conversation;
      } else {
        result = {
          ...conversation,
          messages: conversation.messages.map((m) =>
            m.citations.some(
              (c) =>
                !documents.some(
                  (d) =>
                    d.id === c.source_id &&
                    d.status === "published" &&
                    d.version === c.version,
                ),
            )
              ? {
                  id: m.id,
                  question: m.question,
                  state: "access_changed",
                  citations: [],
                }
              : m,
          ),
        };
      }
    }
  } else if (pathname === "/notifications") result = list([]);
  else if (parts[0] === "admin" || parts[0] === "security") return missing();
  else return missing();
  if (query) {
    const parameters = new URLSearchParams(query);
    const term = parameters.get("q");
    if (result && typeof result === "object" && "results" in result) {
      const collection = result as List<Record<string, unknown>>;
      for (const field of ["classification", "status", "project_id"]) {
        const value = parameters.get(field);
        if (value)
          collection.results = collection.results.filter(
            (item) => item[field] === value,
          );
      }
    }
    if (term && result && typeof result === "object" && "results" in result) {
      const collection = result as List<any>;
      collection.results = collection.results.filter((item) =>
        JSON.stringify(item).toLowerCase().includes(term.toLowerCase()),
      );
    }
  }
  void audits;
  return clone(result) as T;
}
