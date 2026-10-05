import { useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { useSession } from "../app/session";
import { api } from "../services/api";
import { queryClient } from "../app/queryClient";
import {
  PageHeader,
  Resource,
  useResource,
  Modal,
  Field,
  ErrorNotice,
  Badge,
  Empty,
  Pager,
} from "../components/ui";
import type { Person, Approval, Audit, List } from "../types";
function DirectorySelect({
  path,
  label,
  name,
}: {
  path: string;
  label: string;
  name: string;
}) {
  const [search, setSearch] = useState("");
  const query = useResource<List<{ id: string; name: string }>>(
    `${path}?q=${encodeURIComponent(search)}`,
  );
  return (
    <>
      <Field label={`Find ${label.toLowerCase()}`}>
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Type a name to narrow the options"
        />
      </Field>
      <Field label={label}>
        <select name={name} required defaultValue="">
          <option value="">
            {query.isFetching ? "Loading options…" : "Choose an option"}
          </option>
          {!query.isFetching &&
            !query.error &&
            query.data?.results.map((item) => (
              <option value={item.id} key={item.id}>
                {item.name}
              </option>
            ))}
        </select>
      </Field>
      {query.error && <ErrorNotice error={query.error} />}
      {query.data?.next && (
        <p className="fine">Search by name to find more options.</p>
      )}
    </>
  );
}
function AccessFields() {
  const [action, setAction] = useState("project_membership");
  return (
    <>
      <DirectorySelect
        path="/admin/users"
        label="Colleague"
        name="target_user_id"
      />
      <Field label="Assignment">
        <select
          name="action"
          value={action}
          onChange={(event) => setAction(event.target.value)}
        >
          <option value="project_membership">Project membership</option>
          <option value="team_membership">Team membership</option>
          <option value="team_lead">Team lead assignment</option>
        </select>
      </Field>
      <DirectorySelect
        key={action}
        path={
          action === "project_membership" ? "/admin/projects" : "/admin/teams"
        }
        label={action === "project_membership" ? "Project" : "Team"}
        name="scope_id"
      />
      <Field label="Change">
        <select name="operation">
          <option value="assign">Assign</option>
          <option value="revoke">Revoke</option>
        </select>
      </Field>
      <Field label="Expires at">
        <input type="datetime-local" name="expires_at" required />
      </Field>
    </>
  );
}
export function Administration({
  view,
}: {
  view: "users" | "access" | "audit";
}) {
  const session = useSession();
  if (!(session.capabilities.includes(view === "audit" ? "audit" : "admin") || (view === "access" && session.capabilities.includes("approvals"))))
    return (
      <Empty title="Page unavailable">
        This page is unavailable or you no longer have access.
      </Empty>
    );
  return <AdminContent view={view} />;
}
function AdminContent({ view }: { view: "users" | "access" | "audit" }) {
  const session = useSession();
  const [params] = useSearchParams();
  const action = params.get("action") || "";
  const [dialog, setDialog] = useState(session.capabilities.includes("admin") && (view === "users" ? ["invite","team","project"].includes(action) : view === "access" && action === "access") ? action : "");
  const [cursor, setCursor] = useState("");
  const [filter, setFilter] = useState("");
  const [success, setSuccess] = useState("");
  const [invitationUrl, setInvitationUrl] = useState("");
  const path =
    view === "audit"
      ? "/security/audit"
      : view === "access"
        ? "/admin/approvals"
        : "/admin/users";
  const query = useResource<List<Person | Approval | Audit>>(
    `${path}?cursor=${encodeURIComponent(cursor)}&q=${encodeURIComponent(filter)}`,
  );
  const mutation = useMutation({
    mutationFn: ({ path, body }: { path: string; body: unknown }) =>
      api<{ invitation_url?: string }>(path, "POST", body),
    onSuccess: async (result) => {
      setInvitationUrl(result?.invitation_url || "");
      await queryClient.invalidateQueries();
      setDialog("");
      setSuccess(
        "Request recorded. Any required independent approvals must complete before access changes.",
      );
    },
  });
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.currentTarget));
    mutation.mutate({
      path:
        dialog === "invite"
          ? "/admin/invitations"
          : dialog === "team"
            ? "/admin/teams"
            : dialog === "project"
              ? "/admin/projects"
              : "/admin/access-requests",
      body,
    });
  }
  return (
    <>
      <PageHeader
        eyebrow="WORKSPACE MANAGEMENT"
        title={
          view === "users"
            ? "Organization"
            : view === "access"
              ? "Access & approvals"
              : "Audit events"
        }
        description={
          view === "audit"
            ? "Security decisions and policy events. Metadata only."
            : "Manage structure with clear accountability and independent approvals."
        }
        actions={
          view === "users" ? (
            <>
              <button
                className="button secondary"
                onClick={() => setDialog("team")}
              >
                Create team
              </button>
              <button
                className="button secondary"
                onClick={() => setDialog("project")}
              >
                Create project
              </button>
              <button className="button" onClick={() => setDialog("invite")}>
                Invite colleague
              </button>
            </>
          ) : view === "access" && session.capabilities.includes("admin") ? (
            <button className="button" onClick={() => setDialog("access")}>
              Propose access change
            </button>
          ) : null
        }
      />
      <div className="notice">
        Administrative permissions do not grant access to private updates,
        documents, or personal fields.
      </div>
      {success && (
        <div className="notice" role="status">
          {success}
          {invitationUrl && <p>Share this invitation with the colleague: <a href={invitationUrl}>{invitationUrl}</a></p>}
        </div>
      )}
      {mutation.error && <ErrorNotice error={mutation.error} />}
      <div className="toolbar">
        <input
          aria-label="Filter records"
          placeholder="Filter records…"
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value);
            setCursor("");
          }}
        />
      </div>
      <Resource query={query}>
        {(data) => (
          <>
            <section className="panel">
              {data.results.map((record) => (
                <div key={record.id} className="list-row">
                  {"email" in record ? (
                    <>
                      <div>
                        <strong>{record.name}</strong>
                        <small>
                          {record.email} · {record.team}
                        </small>
                      </div>
                      <button
                        className="button secondary"
                        onClick={() => setDialog(`deactivate:${record.id}`)}
                      >
                        Deactivate
                      </button>
                    </>
                  ) : "scope" in record ? (
                    <>
                      <div>
                        <strong>{record.scope}</strong>
                        <small>
                          {record.requester} · {record.reason}
                        </small>
                      </div>
                      <Badge>{record.status}</Badge>
                      {record.can_review && (
                        <button
                          className="button secondary"
                          onClick={() => setDialog(`approve:${record.id}`)}
                        >
                          Review
                        </button>
                      )}
                    </>
                  ) : (
                    <>
                      <div>
                        <strong>{record.action}</strong>
                        <small>
                          Actor {record.actor} · Target {record.target} ·{" "}
                          {record.date}
                        </small>
                        <small>
                          Reason {record.reason} · Policy{" "}
                          {record.policy_version}
                        </small>
                      </div>
                      <Badge
                        tone={record.decision === "allow" ? "green" : "amber"}
                      >
                        {record.decision}
                      </Badge>
                    </>
                  )}
                </div>
              ))}
              {!data.results.length && (
                <Empty
                  title={
                    view === "audit"
                      ? "No matching events"
                      : "Nothing to review yet"
                  }
                />
              )}
            </section>
            <Pager next={data.next} onNext={setCursor} />
          </>
        )}
      </Resource>
      {dialog && !dialog.includes(":") && (
        <Modal
          title={
            dialog === "invite"
              ? "Invite a colleague"
              : dialog === "team"
                ? "Create team"
                : dialog === "project"
                  ? "Create project"
                  : "Propose an access change"
          }
          onClose={() => setDialog("")}
        >
          <form onSubmit={submit}>
            {mutation.error && <ErrorNotice error={mutation.error} />}
            {dialog === "invite" ? (
              <Field label="Work email">
                <input type="email" required name="email" />
              </Field>
            ) : ["team", "project"].includes(dialog) ? (
              <>
                <Field label="Name">
                  <input required name="name" maxLength={150} />
                </Field>
                {dialog === "project" && (
                  <DirectorySelect
                    path="/admin/users"
                    label="Independent project steward"
                    name="steward_user_id"
                  />
                )}
              </>
            ) : (
              <AccessFields />
            )}
            <Field label="Reason">
              <textarea name="reason" required minLength={10} />
            </Field>
            <div className="notice">
              Self-affecting changes require a second organization admin and a
              security reviewer. The server enforces this rule.
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="button secondary"
                onClick={() => setDialog("")}
              >
                Cancel
              </button>
              <button className="button" disabled={mutation.isPending}>
                Submit request
              </button>
            </div>
          </form>
        </Modal>
      )}
      {dialog.includes(":") && (
        <Modal
          title={
            dialog.startsWith("deactivate")
              ? "Deactivate colleague?"
              : "Review approval"
          }
          onClose={() => setDialog("")}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const [action, id] = dialog.split(":");
              mutation.mutate({
                path:
                  action === "deactivate"
                    ? `/admin/users/${id}/deactivate`
                    : `/admin/approvals/${id}/review`,
                body: Object.fromEntries(new FormData(e.currentTarget)),
              });
            }}
          >
            {dialog.startsWith("approve") && (
              <Field label="Decision">
                <select name="decision">
                  <option value="approve">Approve</option>
                  <option value="reject">Reject</option>
                </select>
              </Field>
            )}
            {mutation.error && <ErrorNotice error={mutation.error} />}
            <Field label="Reason">
              <textarea name="reason" required minLength={10} />
            </Field>
            <p>
              Only an independent authorized reviewer can approve an access
              change.
            </p>
            <div className="modal-footer">
              <button
                type="button"
                className="button secondary"
                onClick={() => setDialog("")}
              >
                Cancel
              </button>
              <button className="button" disabled={mutation.isPending}>
                Confirm
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}
