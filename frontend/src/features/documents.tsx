import { useState, type FormEvent } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import {
  Upload,
  FileText,
  Search,
  Download,
  LockKeyhole,
  ArrowUpRight,
  ShieldCheck,
} from "lucide-react";
import { api, download } from "../services/api";
import { demoMode } from "../services/api/client";
import { queryClient } from "../app/queryClient";
import {
  Badge,
  Empty,
  ErrorNotice,
  Field,
  Modal,
  PageHeader,
  Pager,
  Resource,
  useResource,
  date,
} from "../components/ui";
import type { Document, Project, List } from "../types";
const fileAccept = ".pdf,.docx,.txt";
function validateFile(file: File | null) {
  if (!file) throw new Error("Choose a file to upload.");
  if (!/\.(pdf|docx|txt)$/i.test(file.name) || file.size > 10 * 1024 * 1024)
    throw new Error("Choose a PDF, DOCX, or TXT file up to 10 MB.");
  return file;
}
function UploadDialog({
  onClose,
  existing,
}: {
  onClose: () => void;
  existing?: Document;
}) {
  const projects = useResource<List<Project>>("/projects");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<unknown>();
  const upload = useMutation({
    mutationFn: (body: FormData) =>
      api(
        existing ? `/documents/${existing.id}/versions` : "/documents",
        "POST",
        body,
        existing?.version,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      onClose();
    },
  });
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    try {
      const form = new FormData(e.currentTarget);
      form.set("file", validateFile(file));
      upload.mutate(form);
    } catch (err) {
      setError(err);
    }
  }
  return (
    <Modal
      title={
        existing ? "Upload a new version" : "Add to your knowledge library"
      }
      onClose={onClose}
    >
      <form onSubmit={submit}>
        <p className="muted">
          {existing
            ? "The replacement keeps existing classification and grants."
            : "New files start unpublished, visible only to you."}
        </p>
        {demoMode && (
          <div className="notice">
            Demo upload only. File scanning and extraction are simulated; use
            synthetic files.
          </div>
        )}
        {!existing && (
          <>
            <Field label="Document title">
              <input
                name="title"
                required
                maxLength={200}
                placeholder="Give this document a clear name"
              />
            </Field>
            <Resource query={projects}>
              {(data) => (
                <Field label="Project">
                  <select name="project_id" required>
                    {data.results.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </Field>
              )}
            </Resource>
          </>
        )}
        <label className="upload-zone">
          <Upload size={28} />
          <strong>{file ? file.name : "Choose a document"}</strong>
          <span>PDF, DOCX, or TXT · up to 10 MB</span>
          <input
            aria-label="Document file"
            type="file"
            accept={fileAccept}
            required
            onChange={(e) => {
              setFile(e.target.files?.[0] || null);
              setError(undefined);
            }}
          />
        </label>
        {(error || upload.error) && (
          <ErrorNotice error={error || upload.error} />
        )}
        <div className="modal-footer">
          <button type="button" className="button secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="button" disabled={upload.isPending}>
            {upload.isPending ? "Uploading…" : "Upload to private staging"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
export function Documents() {
  const [params] = useSearchParams();
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState("all");
  const [cursor, setCursor] = useState("");
  const [upload, setUpload] = useState(params.get("new") === "1");
  const query = useResource<List<Document>>(
    `/documents?q=${encodeURIComponent(q)}&cursor=${encodeURIComponent(cursor)}${filter === "all" ? "" : `&classification=${filter}`}${params.get("project") ? `&project_id=${encodeURIComponent(params.get("project")!)}` : ""}`,
  );
  return (
    <>
      <PageHeader
        eyebrow="TEAM KNOWLEDGE"
        title="Document library"
        description="A home for the information that moves your work forward."
        actions={
          <button className="button" onClick={() => setUpload(true)}>
            <Upload size={17} /> Upload document
          </button>
        }
      />
      <div className="toolbar">
        <label className="search-input">
          <Search size={17} />
          <input
            placeholder="Find a document…"
            aria-label="Find a document"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setCursor("");
            }}
          />
        </label>
        <select
          aria-label="Classification filter"
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value);
            setCursor("");
          }}
        >
          <option value="all">All classifications</option>
          <option value="project">Project members</option>
          <option value="restricted">Restricted</option>
        </select>
      </div>
      <section className="panel">
        <Resource query={query}>
          {(data) => (
            <>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Document name</th>
                      <th>Project</th>
                      <th>Access</th>
                      <th>Status</th>
                      <th>Updated</th>
                      <th>
                        <span className="sr-only">Open</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.results
                      .filter(
                        (d) =>
                          (filter === "all" || d.classification === filter) &&
                          (!params.get("project") ||
                            d.project_id === params.get("project")),
                      )
                      .map((d) => (
                        <tr key={d.id}>
                          <td>
                            <Link
                              className="document-cell"
                              to={`/documents/${d.id}`}
                            >
                              <span
                                className={`file-icon ${d.type.toLowerCase()}`}
                              >
                                <FileText size={20} />
                              </span>
                              <span>
                                <strong>{d.title}</strong>
                                <small>
                                  {d.type} · {d.size} · v{d.version}
                                </small>
                              </span>
                            </Link>
                          </td>
                          <td>{d.project_name}</td>
                          <td>
                            <Badge
                              tone={
                                d.classification === "restricted"
                                  ? "amber"
                                  : "blue"
                              }
                            >
                              {d.classification === "restricted" && (
                                <LockKeyhole size={11} />
                              )}{" "}
                              {d.classification === "project"
                                ? "Project members"
                                : "Restricted"}
                            </Badge>
                          </td>
                          <td>
                            <Badge
                              tone={
                                d.status === "published" ? "green" : "neutral"
                              }
                            >
                              {d.status.replace("_", " ")}
                            </Badge>
                          </td>
                          <td className="muted">{date(d.updated_at)}</td>
                          <td>
                            <Link
                              to={`/documents/${d.id}`}
                              aria-label={`Open ${d.title}`}
                            >
                              <ArrowUpRight size={17} />
                            </Link>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
              {!data.results.length && (
                <Empty title="No documents found">
                  Try a different search or upload your first document.
                </Empty>
              )}
              <Pager next={data.next} onNext={setCursor} />
            </>
          )}
        </Resource>
      </section>
      <p className="fine">
        <ShieldCheck size={14} /> Documents are available according to your
        current project membership and grants.
      </p>
      {upload && <UploadDialog onClose={() => setUpload(false)} />}
    </>
  );
}
function AccessDialog({
  doc,
  onClose,
  publish,
}: {
  doc: Document;
  onClose: () => void;
  publish: boolean;
}) {
  const [classification, setClassification] = useState(doc.classification);
  const [grants, setGrants] = useState(doc.grants);
  const project = useResource<Project>(`/projects/${doc.project_id}`);
  const mutation = useMutation({
    mutationFn: () =>
      api(
        `/documents/${doc.id}/${publish ? "publish" : "access"}`,
        publish ? "POST" : "PATCH",
        { classification, grants, version: doc.version },
        doc.version,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      onClose();
    },
  });
  const widening =
    doc.status === "published" &&
    doc.classification === "restricted" &&
    classification === "project";
  return (
    <Modal
      title={publish ? "Publish document" : "Manage document access"}
      onClose={onClose}
    >
      <Field label="Classification">
        <select
          value={classification}
          onChange={(e) =>
            setClassification(e.target.value as typeof classification)
          }
        >
          <option value="project">Project · All current project members</option>
          <option value="restricted">
            Restricted · Named current project members
          </option>
        </select>
      </Field>
      {classification === "restricted" && (
        <Resource query={project}>
          {(p) => (
            <fieldset>
              <legend>Named grants</legend>
              {p.members.map((m) => (
                <label className="checkbox-row" key={m.id}>
                  <input
                    type="checkbox"
                    checked={grants.includes(m.id)}
                    onChange={(e) =>
                      setGrants(
                        e.target.checked
                          ? [...grants, m.id]
                          : grants.filter((g) => g !== m.id),
                      )
                    }
                  />
                  <span>
                    {m.name}
                    <small>{m.email}</small>
                  </span>
                </label>
              ))}
            </fieldset>
          )}
        </Resource>
      )}
      <div className="notice">
        <LockKeyhole size={18} />
        <span>
          {widening
            ? "Widening access requires a separate project steward’s approval. This sends a request; it does not publish the change."
            : classification === "project"
              ? "All current members of this project will be able to read the published document."
              : "Only selected current project members can read the published document. The uploader also needs a grant."}
          {!publish &&
            !widening &&
            " Saving suspends publication. Review grants, then publish again."}
        </span>
      </div>
      {mutation.error && <ErrorNotice error={mutation.error} />}
      <div className="modal-footer">
        <button className="button secondary" onClick={onClose}>
          Cancel
        </button>
        <button
          className="button"
          disabled={
            mutation.isPending ||
            (classification === "restricted" && !grants.length) ||
            project.isFetching
          }
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending
            ? "Saving…"
            : widening
              ? "Request steward approval"
              : publish
                ? "Confirm and publish"
                : "Save access"}
        </button>
      </div>
    </Modal>
  );
}
export function DocumentDetail() {
  const { id } = useParams();
  const query = useResource<Document>(`/documents/${id}`);
  const [dialog, setDialog] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<unknown>();
  const [downloading, setDownloading] = useState(false);
  const removal = useMutation({
    mutationFn: (d: Document) =>
      api(
        `/documents/${d.id}/request-deletion`,
        "POST",
        { version: d.version },
        d.version,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      setDialog("");
      setMessage("Removal requested. The retention steward will review it.");
    },
  });
  async function saveFile(d: Document) {
    setDownloading(true);
    setError(undefined);
    try {
      const blob = await download(d.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = demoMode
        ? blob instanceof File
          ? blob.name
          : "synthetic-demo.txt"
        : `${d.title.replace(/[^a-zA-Z0-9 ._-]/g, "_")}.${d.type.toLowerCase()}`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError(e);
    } finally {
      setDownloading(false);
    }
  }
  return (
    <Resource query={query}>
      {(d) => (
        <>
          <Link className="back-link" to="/documents">
            ← Document library
          </Link>
          <PageHeader
            eyebrow={d.project_name.toUpperCase()}
            title={d.title}
            description={`${d.type} · ${d.size} · Version ${d.version} · Updated ${date(d.updated_at)}`}
            actions={
              <>
              {d.status === "processing" && <button className="button secondary" onClick={() => void query.refetch()}>Refresh processing status</button>}
              <button
                className="button"
                disabled={downloading || d.status !== "published"}
                onClick={() => void saveFile(d)}
              >
                <Download size={17} />
                {downloading ? "Checking access…" : "Download"}
              </button>
              </>
            }
          />
          {error && <ErrorNotice error={error} />}
          {message && (
            <div className="notice" role="status">
              {message}
            </div>
          )}
          <div className="two-column">
            <section className="panel document-preview">
              <span className={`file-icon large ${d.type.toLowerCase()}`}>
                <FileText size={42} />
                <small>{d.type}</small>
              </span>
              <h2>{d.title}</h2>
              <p>
                {d.status === "published"
                  ? "Download the current version to read the full document."
                  : d.status === "quarantined"
                    ? "This upload is quarantined and is not available for search or AI."
                    : d.status === "failed"
                      ? "Processing failed. Upload a replacement to try again."
                      : "This document is not currently published."}
              </p>
              <Badge tone={d.status === "published" ? "green" : "amber"}>
                {d.status.replace("_", " ")}
              </Badge>
              {demoMode && (
                <small>
                  Synthetic document preview · No live file processing
                </small>
              )}
            </section>
            <section className="panel detail-panel">
              <h2>Document details</h2>
              <dl>
                <dt>Project</dt>
                <dd>
                  <Link to={`/projects/${d.project_id}`}>{d.project_name}</Link>
                </dd>
                <dt>Uploaded by</dt>
                <dd>{d.uploader_name}</dd>
                <dt>Classification</dt>
                <dd>
                  <Badge
                    tone={d.classification === "restricted" ? "amber" : "blue"}
                  >
                    {d.classification}
                  </Badge>
                </dd>
                <dt>Current version</dt>
                <dd>Version {d.version}</dd>
              </dl>
              <div className="notice">
                <ShieldCheck size={18} /> Every download checks your current
                access.
              </div>
              {d.can_manage && (
                <div className="stack">
                  <button
                    className="button secondary"
                    onClick={() => setDialog("access")}
                  >
                    Manage access
                  </button>
                  {d.status === "unpublished" && (
                    <button
                      className="button"
                      onClick={() => setDialog("publish")}
                    >
                      Publish document
                    </button>
                  )}
                  <button
                    className="button secondary"
                    onClick={() => setDialog("version")}
                  >
                    Upload new version
                  </button>
                  <button
                    className="text-button danger"
                    disabled={d.status === "deletion_requested"}
                    onClick={() => setDialog("delete")}
                  >
                    Request removal
                  </button>
                </div>
              )}
            </section>
          </div>
          {["access", "publish"].includes(dialog) && (
            <AccessDialog
              doc={d}
              publish={dialog === "publish"}
              onClose={() => setDialog("")}
            />
          )}
          {dialog === "version" && (
            <UploadDialog existing={d} onClose={() => setDialog("")} />
          )}
          {dialog === "delete" && (
            <Modal
              title="Request document removal"
              onClose={() => setDialog("")}
            >
              <p>
                A retention steward will review this request. Removal is not
                immediate.
              </p>
              {removal.error && <ErrorNotice error={removal.error} />}
              <div className="modal-footer">
                <button
                  className="button secondary"
                  onClick={() => setDialog("")}
                >
                  Cancel
                </button>
                <button
                  className="button"
                  disabled={removal.isPending}
                  onClick={() => removal.mutate(d)}
                >
                  Send removal request
                </button>
              </div>
            </Modal>
          )}
        </>
      )}
    </Resource>
  );
}
