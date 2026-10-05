import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  NavLink,
  Outlet,
  useNavigate,
  Link,
  useLocation,
} from "react-router-dom";
import {
  LayoutDashboard,
  FolderKanban,
  NotebookPen,
  Users,
  Files,
  Sparkles,
  Settings,
  ShieldCheck,
  Search,
  Bell,
  ChevronsLeft,
  Menu,
  X,
  LogOut,
  ArrowUpRight,
  KeyRound,
  ScrollText,
} from "lucide-react";
import { useSession } from "../app/session";
import { api } from "../services/api";
import { demoMode } from "../services/api/client";
import { Avatar } from "./ui";
export function Layout() {
  const session = useSession();
  const [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [smallScreen, setSmallScreen] = useState(
    () => window.matchMedia("(max-width: 700px)").matches,
  );
  const sidebarRef = useRef<HTMLElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 700px)");
    const change = () => {
      setSmallScreen(media.matches);
      setMobile(false);
    };
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    if (!mobile || !smallScreen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    sidebarRef.current
      ?.querySelector<HTMLButtonElement>(".mobile-close")
      ?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobile(false);
      if (event.key !== "Tab") return;
      const controls = Array.from(
        sidebarRef.current?.querySelectorAll<HTMLElement>("a, button") || [],
      ).filter((el) => el.offsetParent !== null);
      const first = controls[0];
      const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", keydown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", keydown);
      menuButtonRef.current?.focus();
    };
  }, [mobile, smallScreen]);
  const [search, setSearch] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const nav = [
    ["/", "Overview", LayoutDashboard],
    ["/projects", "Projects", FolderKanban],
    ["/work", "Work updates", NotebookPen],
    ["/people", "People", Users],
    ["/documents", "Documents", Files],
    ["/assistant", "AI Assistant", Sparkles],
  ] as const;
  function submit(e: FormEvent) {
    e.preventDefault();
    if (search.trim()) {
      navigate(`/search?q=${encodeURIComponent(search.trim())}`);
      setSearch("");
    }
  }
  return (
    <div className={`app ${collapsed ? "collapsed" : ""}`}>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside
        ref={sidebarRef}
        aria-label="Workspace navigation"
        aria-hidden={smallScreen && !mobile}
        inert={smallScreen && !mobile}
        className={`sidebar ${mobile ? "open" : ""}`}
      >
        <Link className="brand" to="/" onClick={() => setMobile(false)}>
          <span className="brand-icon">
            <ShieldCheck size={23} />
          </span>
          <span className="nav-label">
            Secure<span className="brand-light">AI</span>
          </span>
        </Link>
        <button
          className="mobile-close icon-button"
          aria-label="Close navigation"
          onClick={() => setMobile(false)}
        >
          <X />
        </button>
        <div className="workspace-select">
          <span className="workspace-logo">N</span>
          <div className="nav-label">
            <strong>{session.organization}</strong>
            <small>Team workspace</small>
          </div>
          <span className="workspace-dot nav-label" />
        </div>
        <p className="nav-caption nav-label">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {nav.map(([to, label, Icon]) => (
            <NavLink
              end={to === "/"}
              to={to}
              key={to}
              title={label}
              onClick={() => setMobile(false)}
            >
              <Icon size={19} />
              <span className="nav-label">{label}</span>
              {to === "/assistant" && (
                <span className="tiny-tag nav-label">AI</span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="security-card nav-label">
            <ShieldCheck size={21} />
            <strong>A space you can trust</strong>
            <p>Your workspace shows only information you can access.</p>
          </div>
          <p className="nav-caption nav-label">MANAGE</p>
          <nav aria-label="Workspace settings" onClick={() => setMobile(false)}>
            <NavLink to="/settings">
              <Settings size={19} />
              <span className="nav-label">Settings</span>
            </NavLink>
            {session.capabilities.includes("admin") && (
              <>
                <NavLink to="/admin/users">
                  <Users size={19} />
                  <span className="nav-label">Organization</span>
                </NavLink>
              </>
            )}
            {(session.capabilities.includes("admin") || session.capabilities.includes("approvals")) && (
                <NavLink to="/admin/access">
                  <KeyRound size={19} />
                  <span className="nav-label">Access & approvals</span>
                </NavLink>
            )}
            {session.capabilities.includes("audit") && (
              <NavLink to="/admin/audit">
                <ScrollText size={19} />
                <span className="nav-label">Audit events</span>
              </NavLink>
            )}
          </nav>
          <button
            className="collapse-button"
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <ChevronsLeft size={18} />
            <span className="nav-label">Collapse sidebar</span>
          </button>
        </div>
      </aside>
      {mobile && (
        <button
          className="mobile-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobile(false)}
        />
      )}
      <div className="main-shell" inert={smallScreen && mobile} aria-hidden={smallScreen && mobile}>
        <header className="topbar">
          <button
            className="mobile-menu icon-button"
            ref={menuButtonRef}
            aria-label="Open navigation"
            aria-expanded={mobile}
            onClick={() => setMobile(true)}
          >
            <Menu />
          </button>
          <span className="breadcrumb">
            Workspace <span>/</span>{" "}
            <strong>
              {nav.find(([to]) =>
                to === "/"
                  ? location.pathname === "/"
                  : location.pathname.startsWith(to),
              )?.[1] || "Settings"}
            </strong>
          </span>
          <form className="global-search" onSubmit={submit}>
            <Search size={17} />
            <input
              aria-label="Search workspace"
              placeholder="Search your workspace…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <kbd>↵</kbd>
          </form>
          <div className="topbar-actions">
            <Link
              className="icon-button"
              to="/notifications"
              aria-label="Notifications"
            >
              <Bell size={20} />
            </Link>
            <span className="divider" />
            <Link to="/settings" className="user-menu">
              <Avatar name={session.name} small />
              <span>
                {session.name.split(" ")[0]}
                <small>{session.title}</small>
              </span>
            </Link>
            <button
              className="icon-button"
              aria-label="Sign out"
              disabled={loggingOut}
              onClick={async () => {
                setLoggingOut(true);
                try {
                  await api("/auth/logout", "POST");
                  window.dispatchEvent(new Event("signed-out"));
                } catch {
                  setLoggingOut(false);
                  alert("Sign out failed. Please try again.");
                }
              }}
            >
              <LogOut size={17} />
            </button>
          </div>
        </header>
        {demoMode && (
          <div className="demo-banner">
            <span>
              <span className="demo-dot" /> Synthetic demo · Changes reset on
              refresh
            </span>
            <span>
              No live company data or AI <ArrowUpRight size={13} />
            </span>
          </div>
        )}
        <main id="main" tabIndex={-1}>
          <Outlet />
        </main>
        <footer className="app-footer">
          <span>SecureAI workspace</span>
          <span>
            <ShieldCheck size={13} /> Access is checked for every request
          </span>
        </footer>
      </div>
    </div>
  );
}
