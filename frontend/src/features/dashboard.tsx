import { Link, useSearchParams } from "react-router-dom";
import { ArrowRight, ArrowUpRight, FileText, Plus, Sparkles, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";
import { useSession } from "../app/session";
import { useResource, Resource, PageHeader, Badge, date } from "../components/ui";
import type { DashboardData, DashboardView, Update, Audit } from "../types";

const labels: Record<DashboardView, string> = { employee: "Personal workspace", lead: "Team lead", admin: "Organization admin", security: "Security overview" };
const titles: Record<DashboardView, string> = { employee: "Employee dashboard", lead: "Team lead dashboard", admin: "Organization admin dashboard", security: "Security dashboard" };
const descriptions: Record<DashboardView, string> = {
  employee: "Your drafts, published updates, assigned projects and accessible documents.",
  lead: "Updates and blockers shared with you by the teams you currently lead.",
  admin: "Organization accounts, invitations, teams, projects and access approvals.",
  security: "Access denials, security events, permission changes and scan failures.",
};
const metrics: Record<DashboardView, [string,string,string][]> = {
  employee: [["drafts","My drafts","/work?status=draft"],["published","My published updates","/work?status=published"],["projects","Assigned projects","/projects"],["documents","Accessible documents","/documents"]],
  lead: [["teams","Teams I lead","#team-updates"],["updates_today","Team updates today","#team-updates"],["blockers","Lead-visible blockers","#blockers"],["projects","My assigned projects","/projects"]],
  admin: [["accounts","Active accounts","/admin/users"],["invitations","Pending invitations","#invitations"],["teams","Teams","/admin/users?action=team"],["projects","Projects","/admin/users?action=project"]],
  security: [["denials","Access denials","#audit-timeline"],["events","Security events","#audit-timeline"],["permissions","Permission changes","#permission-changes"],["failed_scans","Failed document scans","#audit-timeline"]],
};

function Panel({title,children,to,id}: {title:string;children:ReactNode;to?:string;id?:string}) {
  return <section className="panel" id={id}><div className="section-heading"><h2>{title}</h2>{to && <Link to={to}>View all <ArrowRight size={15}/></Link>}</div><div className="panel-padding">{children}</div></section>;
}
function UpdateRows({rows}: {rows:Update[]}) {
  return rows.length ? <div>{rows.map(u=><Link className="activity-row" to={`/work/${u.id}`} key={u.id}><div><div className="row-title">{u.owner_name} · {u.team_name} <Badge tone={u.status === "draft" ? "amber" : "green"}>{u.status}</Badge>{u.is_blocked && <Badge tone="amber">Blocked</Badge>}</div><p className="line-clamp">{u.body}</p><small>{date(u.work_date)} · {u.visibility === "private" ? "Private" : "Lead visible"}</small></div><ArrowUpRight size={16}/></Link>)}</div> : <p className="muted">No updates available for this view.</p>;
}
function Events({rows}: {rows:Audit[]}) {
  return rows.length ? <ol className="dashboard-timeline">{rows.map(e=><li key={e.id}><div className="row-title"><strong>{e.action.replaceAll("."," ")}</strong><Badge tone={e.decision === "deny" ? "amber" : "green"}>{e.decision}</Badge></div><p>{e.reason}</p><small>{new Date(e.date).toLocaleString()} · Actor {e.actor || "System"}</small><details><summary>Event metadata</summary><p>Target: {e.target}</p><p>Policy: {e.policy_version}</p></details></li>)}</ol> : <p className="muted">No matching events.</p>;
}
function AIEntry({team=false}: {team?:boolean}) {
  return <section className="assistant-promo dashboard-ai"><div className="spark-icon"><Sparkles size={22}/></div><Badge tone="purple">YOUR KNOWLEDGE COMPANION</Badge><h2>{team ? "Clarity for your team." : "Less searching. More knowing."}</h2><p>{team ? "Ask about team information you can currently access. Private drafts and private employee updates stay private." : "Ask a question grounded in your accessible updates, projects and documents."}</p><Link className="text-button" to="/assistant">Ask SecureAI <ArrowUpRight size={17}/></Link></section>;
}

export function Dashboard() {
  const session=useSession();
  const [params,setParams]=useSearchParams();
  const queryParams=new URLSearchParams();
  for (const key of ["view","date","event"]) if (params.get(key)) queryParams.set(key,params.get(key)!);
  const query=useResource<DashboardData>(`/dashboard?${queryParams}`);
  function filter(key:string,value:string) { const next=new URLSearchParams(params); value ? next.set(key,value) : next.delete(key); setParams(next); }
  return <><PageHeader eyebrow="YOUR WORKSPACE, CONNECTED" title={`Welcome back, ${session.name.split(" ")[0]}`} description="The work and information that matter for your role."/><Resource query={query}>{data=><>
    <section className={`dashboard-role-banner dashboard-role-${data.view}`} aria-label="Current dashboard">
      <div><p className="fine">SIGNED IN AS {session.name}</p><h2>{titles[data.view]}</h2><p>{descriptions[data.view]}</p></div>
      <Badge tone={data.view === "admin" ? "blue" : data.view === "security" ? "purple" : "green"}>{labels[data.view]}</Badge>
      {data.view === "employee" && data.available_views.includes("admin") && <p className="dashboard-role-hint">You are viewing your personal workspace. <button className="text-button" onClick={()=>setParams({view:"admin"})}>Open organization admin dashboard <ArrowRight size={16}/></button></p>}
    </section>
    <div className="toolbar dashboard-toolbar"><nav className="tabs" aria-label="Dashboard views">{data.available_views.map(view=><button key={view} className={data.view===view ? "active" : ""} aria-pressed={data.view===view} onClick={()=>setParams({view})}>{labels[view]}</button>)}</nav>{["lead","security"].includes(data.view) && <label className="dashboard-filter">{data.view === "lead" ? "Update date" : "Event date"}<input type="date" value={data.date} onChange={e=>filter("date",e.target.value)}/></label>}{data.view === "security" && <label className="dashboard-filter">Event type<select value={data.event} onChange={e=>filter("event",e.target.value)}>{[["all","All security events"],["denials","Access denials"],["permissions","Permission changes"],["scans","Document scans"],["sessions","Sign-in activity"]].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>}</div>
    <div className="stats-grid dashboard-stats">{metrics[data.view].map(([key,label,to])=><Link key={key} className="stat-card" to={to}><span className="stat-icon blue"><ShieldCheck size={20}/></span><span><span className="stat-label">{label}</span><strong>{data.cards[key] ?? 0}</strong><small>{data.view === "security" || key === "blockers" ? `For ${date(data.date)}` : key === "updates_today" ? "Today, in your workspace time zone" : "Within your access"}</small></span><ArrowUpRight size={17}/></Link>)}</div>
    <div className="dashboard-actions" aria-label="Quick actions">
      {(data.view === "employee" || data.view === "lead") && <><Link className="button" to="/work?new=1"><Plus size={16}/>Create update</Link>{data.view === "employee" ? <Link className="button secondary" to="/documents?new=1">Upload to assigned project</Link> : <a className="button secondary" href="#team-updates">Read team updates</a>}<Link className="button secondary" to="/assistant">Ask AI</Link></>}
      {data.view === "admin" && <>{[["Invite user","/admin/users?action=invite"],["Deactivate user","/admin/users"],["Manage teams","/admin/users?action=team"],["Manage projects","/admin/users?action=project"],["Assign memberships","/admin/access?action=access"]].map(([label,to])=><Link className="button secondary" key={to} to={to}>{label}</Link>)}</>}
      {data.view === "security" && <><Link className="button" to="/admin/audit">Inspect audit metadata</Link><a className="button secondary" href="#security-settings">Review security settings</a></>}
    </div>
    {data.view === "employee" && <><div className="dashboard-grid"><section className="welcome-card"><div className="welcome-content"><span className="hero-tag">YOUR PERSONAL WORKSPACE</span><h2>Make room for your best work.</h2><p>Capture progress, find shared knowledge, and keep your next step clear.</p><Link className="button light" to="/projects">Explore your projects <ArrowRight size={16}/></Link></div></section><AIEntry/></div><div className="two-column"><Panel title="My recent updates" to="/work"><UpdateRows rows={data.updates || []}/></Panel><Panel title="My projects" to="/projects">{data.projects?.length ? data.projects.map(p=><Link className="mini-project" key={p.id} to={`/projects/${p.id}`}><span className={`project-logo ${p.color}`}>{p.code}</span><div><strong>{p.name}</strong><p>{p.description}</p><Badge tone="green">{p.status}</Badge></div></Link>):<p className="muted">No assigned projects yet.</p>}</Panel></div><Panel title="Recently available documents" to="/documents"><div className="document-strip">{data.documents?.length ? data.documents.map(d=><Link key={d.id} to={`/documents/${d.id}`}><FileText size={22}/><strong>{d.title}</strong><p>{d.project_name} · {date(d.updated_at)}</p><Badge>{d.status}</Badge></Link>):<p className="muted">No accessible documents yet.</p>}</div></Panel></>}
    {data.view === "lead" && <><div className="two-column"><Panel title="Team updates grouped by team" id="team-updates">{data.teams?.map(t=><section key={t.id} className="dashboard-team"><div className="section-heading"><h3>{t.name} <Badge>{t.count}</Badge></h3><Link to={`/work?team=${t.id}`}>Read team updates</Link></div><UpdateRows rows={t.updates}/>{t.count>t.updates.length && <p className="fine">Showing the latest {t.updates.length} updates for this date.</p>}</section>)}</Panel><Panel title="Accessible blockers" id="blockers"><UpdateRows rows={data.blockers || []}/><p className="fine">Published, lead-visible updates marked as blocked on the selected date.</p></Panel></div><div className="two-column"><Panel title="Personal workspace" to="/?view=employee"><UpdateRows rows={data.updates || []}/></Panel><AIEntry team/></div></>}
    {data.view === "admin" && <><div className="two-column"><Panel title="Account status" to="/admin/users">{data.accounts?.map(u=><div className="activity-row" key={u.id}><div><strong>{u.name}</strong><p>{u.email}</p></div><Badge tone={u.active ? "green" : "amber"}>{u.active ? "Active" : "Deactivated"}</Badge></div>)}</Panel><Panel title="Assignment requests & administrative approvals" to="/admin/access">{data.approvals?.length ? data.approvals.map(a=><Link className="activity-row" to="/admin/access" key={a.id}><div><strong>{a.requester}</strong><p>{a.reason}</p><small>{a.scope}</small></div><Badge>{a.status}</Badge></Link>):<p className="muted">No pending approvals available to you.</p>}</Panel></div><div className="two-column"><Panel title="Pending invitations" id="invitations">{data.invitations?.length ? data.invitations.map(i=><div className="activity-row" key={i.id}><div><strong>{i.email}</strong><p>Expires {date(i.expires_at)}</p></div><Badge tone="amber">Pending</Badge></div>):<p className="muted">No pending invitations.</p>}</Panel><Panel title="Membership changes & administrative activity"><p className="fine">Your administrative events. Content access remains separately authorized.</p><Events rows={data.events || []}/></Panel></div></>}
    {data.view === "security" && <><div className="two-column"><Panel title="Audit-event timeline" id="audit-timeline" to="/admin/audit"><Events rows={data.events || []}/><p className="fine">Latest 30 matching events for the selected date. Full audit history is available above.</p></Panel><Panel title="Grant & revocation activity" id="permission-changes"><Events rows={data.changes || []}/></Panel></div><Panel title="Security settings" id="security-settings"><p className="fine">Read-only configuration summary. Unapproved or unconfigured settings are shown explicitly.</p><dl className="dashboard-settings">{data.security_settings?.map(s=><div key={s.name}><dt>{s.name}</dt><dd>{s.value}</dd></div>)}</dl></Panel></>}
  </>}</Resource></>;
}
