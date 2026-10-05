import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowUpRight,
  FolderKanban,
  Users,
  Search,
  FileText,
} from "lucide-react";
import {
  Avatar,
  Badge,
  Empty,
  PageHeader,
  Resource,
  useResource,
  Pager,
} from "../components/ui";
import type { List, Project, Document } from "../types";
export function Projects() {
  const [q, setQ] = useState("");
  const [cursor, setCursor] = useState("");
  const query = useResource<List<Project>>(
    `/projects?q=${encodeURIComponent(q)}&cursor=${encodeURIComponent(cursor)}`,
  );
  return (
    <>
      <PageHeader
        eyebrow="SHARED SPACES"
        title="Your projects"
        description="The people, context, and knowledge behind your work."
      />
      <div className="toolbar">
        <label className="search-input">
          <Search size={17} />
          <input
            aria-label="Find a project"
            placeholder="Find a project…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setCursor("");
            }}
          />
        </label>
        <Badge tone="blue">
          <FolderKanban size={13} /> Your memberships
        </Badge>
      </div>
      <Resource query={query}>
        {(data) => (
          <>
            <div className="project-grid">
              {data.results.map((p) => (
                <Link
                  key={p.id}
                  className="project-card panel"
                  to={`/projects/${p.id}`}
                >
                  <div className="spread">
                    <span className={`project-logo ${p.color}`}>{p.code}</span>
                    <ArrowUpRight size={19} />
                  </div>
                  <h2>{p.name}</h2>
                  <p>{p.description}</p>
                  <div className="spread">
                    <div className="avatar-stack">
                      {p.members.slice(0, 4).map((m) => (
                        <Avatar small key={m.id} name={m.name} />
                      ))}
                    </div>
                    <Badge tone="green">{p.status}</Badge>
                  </div>
                </Link>
              ))}
            </div>
            {!data.results.length && (
              <Empty title="No projects found">
                Try another search or ask your workspace administrator about
                membership.
              </Empty>
            )}
            <Pager next={data.next} onNext={setCursor} />
          </>
        )}
      </Resource>
    </>
  );
}
export function ProjectDetail() {
  const { id } = useParams();
  const query = useResource<Project>(`/projects/${id}`);
  const docs = useResource<List<Document>>(`/projects/${id}/documents`);
  return (
    <Resource query={query}>
      {(p) => (
        <>
          <Link className="back-link" to="/projects">
            ← All projects
          </Link>
          <PageHeader
            eyebrow="PROJECT WORKSPACE"
            title={p.name}
            description={p.description}
            actions={<Badge tone="green">{p.status}</Badge>}
          />
          <div className="two-column">
            <section className="panel">
              <div className="section-heading">
                <h2>
                  <FileText size={19} /> Project documents
                </h2>
                <Link to={`/documents?project=${p.id}`}>Open library</Link>
              </div>
              <Resource query={docs}>
                {(data) => (
                  <>
                    {data.results.map((d) => (
                      <Link
                        className="list-row"
                        to={`/documents/${d.id}`}
                        key={d.id}
                      >
                        <FileText size={21} />
                        <div>
                          <strong>{d.title}</strong>
                          <small>
                            Version {d.version} · {d.classification}
                          </small>
                        </div>
                        <ArrowUpRight size={16} />
                      </Link>
                    ))}
                    {!data.results.length && <Empty title="No documents yet" />}
                  </>
                )}
              </Resource>
            </section>
            <section className="panel">
              <div className="section-heading">
                <h2>
                  <Users size={19} /> Project members
                </h2>
              </div>
              {p.members.map((m) => (
                <Link className="list-row" to={`/people/${m.id}`} key={m.id}>
                  <Avatar name={m.name} small />
                  <div>
                    <strong>{m.name}</strong>
                    <small>{m.title}</small>
                  </div>
                </Link>
              ))}
              <div className="panel-note">Project steward: {p.steward}</div>
            </section>
          </div>
        </>
      )}
    </Resource>
  );
}
