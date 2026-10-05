import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  FileText,
  FolderKanban,
  NotebookPen,
  Plus,
  Sparkles,
  LockKeyhole,
  Users,
  CalendarDays,
} from "lucide-react";
import { useSession } from "../app/session";
import {
  useResource,
  Resource,
  PageHeader,
  Badge,
  date,
} from "../components/ui";
import type { Project, Update, Document, List } from "../types";
export function Dashboard() {
  const session = useSession();
  const projects = useResource<List<Project>>("/projects");
  const updates = useResource<List<Update>>("/updates");
  const docs = useResource<List<Document>>("/documents");
  return (
    <>
      <PageHeader
        eyebrow="YOUR WORKSPACE, CONNECTED"
        title={`Welcome back, ${session.name.split(" ")[0]}`}
        description="A little clarity for the work ahead."
        actions={
          <Link className="button" to="/work?new=1">
            <Plus size={17} /> New update
          </Link>
        }
      />
      <div className="dashboard-grid">
        <section className="welcome-card">
          <div className="welcome-content">
            <span className="hero-tag">
              <span /> MAKE ROOM FOR YOUR BEST WORK
            </span>
            <h2>
              Everything you need.
              <br />
              Right where you need it.
            </h2>
            <p>
              Keep your team in the loop, find the right information,
              <br className="desktop-only" /> and move your work forward with
              confidence.
            </p>
            <Link to="/projects" className="button light">
              Explore your projects <ArrowRight size={16} />
            </Link>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="art-tile tile-doc">
              <FileText />
            </div>
            <div className="art-tile tile-shield">
              <ShieldSymbol />
            </div>
            <div className="art-tile tile-spark">
              <Sparkles />
            </div>
            <span className="art-dot dot-one" />
            <span className="art-dot dot-two" />
          </div>
        </section>
        <section className="assistant-promo">
          <div className="spark-icon">
            <Sparkles size={22} />
          </div>
          <Badge tone="purple">YOUR KNOWLEDGE COMPANION</Badge>
          <h2>
            Less searching.
            <br />
            More knowing.
          </h2>
          <p>
            Ask a question. Get a clear answer, grounded in your accessible
            sources.
          </p>
          <Link className="text-button" to="/assistant">
            Ask SecureAI <ArrowUpRight size={17} />
          </Link>
        </section>
      </div>
      <div className="stats-grid">
        {[
          {
            label: "Your projects",
            data: projects,
            Icon: FolderKanban,
            to: "/projects",
            color: "blue",
            note: "Spaces you’re a part of",
          },
          {
            label: "Work updates",
            data: updates,
            Icon: NotebookPen,
            to: "/work",
            color: "violet",
            note: "Your progress, captured",
          },
          {
            label: "Documents",
            data: docs,
            Icon: FileText,
            to: "/documents",
            color: "amber",
            note: "Knowledge you can access",
          },
        ].map(({ label, data, Icon, to, color, note }) => (
          <Link className="stat-card" to={to} key={label}>
            <span className={`stat-icon ${color}`}>
              <Icon size={20} />
            </span>
            <span>
              <span className="stat-label">{label}</span>
              <strong>
                {data.isFetching
                  ? "…"
                  : data.data
                    ? data.data.next
                      ? `${data.data.results.length}+`
                      : data.data.results.length
                    : "—"}
              </strong>
              <small>{note}</small>
            </span>
            <ArrowUpRight size={17} />
          </Link>
        ))}
      </div>
      <div className="two-column">
        <section className="panel">
          <div className="section-heading">
            <h2>Recent work updates</h2>
            <Link to="/work">
              View all <ArrowRight size={15} />
            </Link>
          </div>
          <Resource query={updates}>
            {(data) => (
              <div>
                {data.results.slice(0, 3).map((update) => (
                  <Link
                    className="activity-row"
                    to={`/work/${update.id}`}
                    key={update.id}
                  >
                    <span className="activity-icon">
                      <NotebookPen size={18} />
                    </span>
                    <div>
                      <div className="row-title">
                        {update.team_name} update{" "}
                        <Badge
                          tone={update.status === "draft" ? "amber" : "green"}
                        >
                          {update.status}
                        </Badge>
                      </div>
                      <p className="line-clamp">{update.body}</p>
                      <small>
                        <CalendarDays size={12} />
                        {date(update.work_date)}
                        <span>·</span>
                        {update.visibility === "private" ? (
                          <LockKeyhole size={12} />
                        ) : (
                          <Users size={12} />
                        )}{" "}
                        {update.visibility === "private"
                          ? "Only you"
                          : "You and your team lead"}
                      </small>
                    </div>
                  </Link>
                ))}
                {!data.results.length && (
                  <p className="panel-padding muted">
                    Your first update starts here.
                  </p>
                )}
              </div>
            )}
          </Resource>
        </section>
        <section className="panel">
          <div className="section-heading">
            <h2>Your projects</h2>
            <Link to="/projects">
              View all <ArrowRight size={15} />
            </Link>
          </div>
          <Resource query={projects}>
            {(data) => (
              <div className="panel-padding">
                {data.results.map((p) => (
                  <Link
                    className="mini-project"
                    key={p.id}
                    to={`/projects/${p.id}`}
                  >
                    <span className={`project-logo ${p.color}`}>{p.code}</span>
                    <div>
                      <strong>{p.name}</strong>
                      <p>{p.description}</p>
                      <Badge tone="green">{p.status}</Badge>
                    </div>
                    <ArrowUpRight size={17} />
                  </Link>
                ))}
              </div>
            )}
          </Resource>
          <div className="panel-note">
            <LockKeyhole size={15} /> A shared space. Thoughtfully protected.
          </div>
        </section>
      </div>
      <section className="panel recent-documents">
        <div className="section-heading">
          <h2>Recently updated documents</h2>
          <Link to="/documents">
            Open library <ArrowRight size={15} />
          </Link>
        </div>
        <Resource query={docs}>
          {(data) => (
            <div className="document-strip">
              {data.results.slice(0, 3).map((d) => (
                <Link key={d.id} to={`/documents/${d.id}`}>
                  <span className={`file-icon ${d.type.toLowerCase()}`}>
                    <FileText size={23} />
                    <small>{d.type}</small>
                  </span>
                  <strong>{d.title}</strong>
                  <p>
                    {d.project_name} <span>·</span> {date(d.updated_at)}
                  </p>
                  <Badge
                    tone={d.classification === "restricted" ? "amber" : "blue"}
                  >
                    {d.classification === "restricted"
                      ? "Restricted"
                      : "Project members"}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </Resource>
      </section>
    </>
  );
}
function ShieldSymbol() {
  return (
    <svg width="50" height="56" viewBox="0 0 50 56" fill="none">
      <path
        d="M25 3 45 11V27C45 40 25 52 25 52S5 40 5 27V11L25 3Z"
        stroke="currentColor"
        strokeWidth="3"
      />
      <path
        d="m16 27 6 6 13-14"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
