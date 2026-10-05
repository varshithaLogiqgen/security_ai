import { useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  Plus,
  LockKeyhole,
  Users,
  NotebookPen,
  Pencil,
  Trash2,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { api } from "../services/api";
import { queryClient } from "../app/queryClient";
import { useSession } from "../app/session";
import {
  Badge,
  PageHeader,
  Resource,
  useResource,
  Empty,
  Modal,
  Field,
  ErrorNotice,
  date,
  Pager,
} from "../components/ui";
import type { Update, List } from "../types";
const schema = z.object({
  team_id: z.string().min(1),
  work_date: z.string().min(1),
  body: z
    .string()
    .trim()
    .min(10, "Write at least 10 characters.")
    .max(10000, "Keep updates under 10,000 characters."),
});
function UpdateForm({
  update,
  onClose,
}: {
  update?: Update;
  onClose: () => void;
}) {
  const session = useSession();
  const navigate = useNavigate();
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      team_id: update?.team_id || session.teams[0]?.id || "",
      work_date: update?.work_date || new Date().toLocaleDateString("en-CA"),
      body: update?.body || "",
    },
  });
  const save = useMutation({
    mutationFn: (values: z.infer<typeof schema>) =>
      api<Update>(
        update ? `/updates/${update.id}` : "/updates",
        update ? "PATCH" : "POST",
        { ...values, ...(update ? { version: update.version } : {}) },
        update?.version,
      ),
    onSuccess: async (u) => {
      await queryClient.invalidateQueries();
      onClose();
      navigate(`/work/${u.id}`);
    },
  });
  return (
    <Modal
      title={update ? "Edit work update" : "Capture your progress"}
      onClose={onClose}
    >
      <form onSubmit={form.handleSubmit((v) => save.mutate(v))}>
        <p className="muted">
          {update?.status === "published"
            ? "Saving creates a new revision. Existing visibility is preserved."
            : "Start with a private draft. You choose who can read it when you publish."}
        </p>
        <div className="form-grid">
          <Field label="Team">
            <select {...form.register("team_id")} disabled={!!update}>
              {session.teams.map((t) => (
                <option value={t.id} key={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Work date">
            <input type="date" required {...form.register("work_date")} />
          </Field>
        </div>
        <Field label="What did you work on?">
          <textarea
            rows={7}
            placeholder="Progress, decisions, blockers, and what’s next…"
            {...form.register("body")}
          />
        </Field>
        {form.formState.errors.body && (
          <p className="field-error" role="alert">
            {form.formState.errors.body.message}
          </p>
        )}
        {save.error && <ErrorNotice error={save.error} />}
        <div className="modal-footer">
          <button type="button" className="button secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="button"
            disabled={save.isPending || !session.teams.length}
          >
            {save.isPending
              ? "Saving…"
              : update
                ? "Save revision"
                : "Save private draft"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
export function Updates() {
  const session = useSession();
  const [params, setParams] = useSearchParams();
  const [filter, setFilter] = useState("all");
  const [team, setTeam] = useState("");
  const [cursor, setCursor] = useState("");
  const query = useResource<List<Update>>(
    team
      ? `/teams/${team}/updates?cursor=${encodeURIComponent(cursor)}${filter === "all" ? "" : `&status=${filter}`}`
      : `/updates?cursor=${encodeURIComponent(cursor)}${filter === "all" ? "" : `&status=${filter}`}`,
  );
  return (
    <>
      <PageHeader
        eyebrow="PROGRESS, CAPTURED"
        title="Work updates"
        description="Keep a record of your day. Share what matters with your lead."
        actions={
          <button className="button" onClick={() => setParams({ new: "1" })}>
            <Plus size={17} /> New update
          </button>
        }
      />
      <div className="toolbar">
        <div className="tabs">
          {["all", "published", "draft"].map((f) => (
            <button
              className={filter === f ? "active" : ""}
              onClick={() => {
                setFilter(f);
                setCursor("");
              }}
              key={f}
            >
              {f === "all"
                ? "All updates"
                : f === "draft"
                  ? "Drafts"
                  : "Published"}
            </button>
          ))}
        </div>
        {session.led_teams.length > 0 && (
          <select
            aria-label="Update scope"
            value={team}
            onChange={(e) => {
              setTeam(e.target.value);
              setCursor("");
            }}
          >
            <option value="">My updates</option>
            {session.led_teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} · Lead view
              </option>
            ))}
          </select>
        )}
      </div>
      <Resource query={query}>
        {(data) => (
          <>
            <div className="update-list">
              {data.results
                .filter((u) => filter === "all" || u.status === filter)
                .map((u) => (
                  <Link
                    className="panel update-card"
                    to={`/work/${u.id}`}
                    key={u.id}
                  >
                    <div className="update-card-top">
                      <span className="activity-icon">
                        <NotebookPen size={20} />
                      </span>
                      <div>
                        <h2>{u.team_name} update</h2>
                        <small>
                          {date(u.work_date)} · {u.owner_name}
                        </small>
                      </div>
                      <Badge tone={u.status === "draft" ? "amber" : "green"}>
                        {u.status.replace("_", " ")}
                      </Badge>
                    </div>
                    <p>{u.body}</p>
                    <div className="update-card-bottom">
                      <span>
                        {u.visibility === "private" ? (
                          <LockKeyhole size={14} />
                        ) : (
                          <Users size={14} />
                        )}{" "}
                        {u.visibility === "private"
                          ? "Only you"
                          : "You and your current team lead"}
                      </span>
                      <span>Version {u.version} →</span>
                    </div>
                  </Link>
                ))}
            </div>
            {!data.results.filter(
              (u) => filter === "all" || u.status === filter,
            ).length && (
              <Empty title="No updates here yet">
                Capture your progress with a new private draft.
              </Empty>
            )}
            <Pager next={data.next} onNext={setCursor} />
          </>
        )}
      </Resource>
      {params.has("new") && <UpdateForm onClose={() => setParams({})} />}
    </>
  );
}
export function UpdateDetail() {
  const { id } = useParams();
  const session = useSession();
  const query = useResource<Update>(`/updates/${id}`);
  const [edit, setEdit] = useState(false);
  const [action, setAction] = useState("");
  const [visibility, setVisibility] = useState<"private" | "lead_visible">(
    "private",
  );
  const navigate = useNavigate();
  const mutate = useMutation({
    mutationFn: ({ u, action }: { u: Update; action: string }) =>
      api(
        `/updates/${u.id}${action === "publish" ? "/publish" : action === "request-deletion" ? "/request-deletion" : ""}`,
        action === "delete"
          ? "DELETE"
          : action === "visibility"
            ? "PATCH"
            : "POST",
        { version: u.version, visibility },
        u.version,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      setAction("");
      if (action === "delete") navigate("/work");
    },
  });
  return (
    <Resource query={query}>
      {(u) => (
        <>
          <Link className="back-link" to="/work">
            ← Work updates
          </Link>
          <PageHeader
            title={`${u.team_name} update`}
            description={`${date(u.work_date)} · ${u.owner_name} · Version ${u.version}`}
            actions={
              <Badge tone={u.status === "draft" ? "amber" : "green"}>
                {u.status.replace("_", " ")}
              </Badge>
            }
          />
          <section className="panel detail-panel">
            <div className="notice">
              <LockKeyhole size={17} />
              {u.status === "draft" || u.visibility === "private"
                ? "Only you can read this update."
                : "You and your current team lead can read this published update."}
            </div>
            <p className="prose">{u.body}</p>
            {u.owner_id === session.id && u.status !== "deletion_requested" && (
              <div className="actions">
                <button
                  className="button secondary"
                  onClick={() => setEdit(true)}
                >
                  <Pencil size={16} /> Edit update
                </button>
                <button
                  className="button"
                  onClick={() => {
                    setVisibility(u.visibility);
                    setAction(u.status === "draft" ? "publish" : "visibility");
                  }}
                >
                  {u.status === "draft"
                    ? "Publish update"
                    : "Change visibility"}
                </button>
                <button
                  className="button danger subtle"
                  onClick={() =>
                    setAction(
                      u.status === "draft" ? "delete" : "request-deletion",
                    )
                  }
                >
                  <Trash2 size={16} />
                  {u.status === "draft" ? "Delete draft" : "Request removal"}
                </button>
              </div>
            )}
          </section>
          {u.revisions.length > 0 && (
            <section className="panel detail-panel">
              <h2>Revision history</h2>
              {u.revisions.map((r) => (
                <details key={r.version}>
                  <summary>
                    Version {r.version} · {date(r.date)}
                  </summary>
                  <p className="prose">{r.body}</p>
                </details>
              ))}
            </section>
          )}
          {edit && <UpdateForm update={u} onClose={() => setEdit(false)} />}
          {action && (
            <Modal
              title={
                action === "delete"
                  ? "Delete this draft?"
                  : action === "request-deletion"
                    ? "Request removal"
                    : action === "publish"
                      ? "Publish your update"
                      : "Change visibility"
              }
              onClose={() => setAction("")}
            >
              {["publish", "visibility"].includes(action) ? (
                <>
                  <Field label="Who can read this update?">
                    <select
                      value={visibility}
                      onChange={(e) =>
                        setVisibility(e.target.value as typeof visibility)
                      }
                    >
                      <option value="private">Private · Only you</option>
                      <option value="lead_visible">
                        Lead visible · You and your current team lead
                      </option>
                    </select>
                  </Field>
                  <div className="notice">
                    {visibility === "private"
                      ? "Only you will be able to read this update."
                      : "Your current team lead will be able to read this update. Other teammates will not."}
                  </div>
                </>
              ) : (
                <p>
                  {action === "delete"
                    ? "This permanently removes your unpublished draft."
                    : "This sends a request through the retention workflow. It does not immediately erase the update."}
                </p>
              )}
              {mutate.error && <ErrorNotice error={mutate.error} />}
              <div className="modal-footer">
                <button
                  className="button secondary"
                  onClick={() => setAction("")}
                >
                  Cancel
                </button>
                <button
                  className="button"
                  disabled={mutate.isPending}
                  onClick={() => mutate.mutate({ u, action })}
                >
                  {mutate.isPending ? "Saving…" : "Confirm"}
                </button>
              </div>
            </Modal>
          )}
        </>
      )}
    </Resource>
  );
}
