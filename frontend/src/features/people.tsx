import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Mail, Search, LockKeyhole } from "lucide-react";
import { useSession } from "../app/session";
import { api } from "../services/api";
import { queryClient } from "../app/queryClient";
import {
  Avatar,
  PageHeader,
  Resource,
  useResource,
  Empty,
  Field,
  ErrorNotice,
  Pager,
} from "../components/ui";
import type { Person, List } from "../types";
export function People() {
  const [q, setQ] = useState("");
  const [cursor, setCursor] = useState("");
  const query = useResource<List<Person>>(
    `/profiles?q=${encodeURIComponent(q)}&cursor=${encodeURIComponent(cursor)}`,
  );
  return (
    <>
      <PageHeader
        eyebrow="BETTER, TOGETHER"
        title="People"
        description="Find a familiar face or make a new connection."
      />
      <div className="toolbar">
        <label className="search-input">
          <Search size={17} />
          <input
            aria-label="Find a colleague"
            placeholder="Search name, title, or team…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setCursor("");
            }}
          />
        </label>
      </div>
      <Resource query={query}>
        {(data) => (
          <>
            <div className="people-grid">
              {data.results.map((p) => (
                <Link
                  to={`/people/${p.id}`}
                  className="person-card panel"
                  key={p.id}
                >
                  <Avatar name={p.name} />
                  <h2>{p.name}</h2>
                  <p>{p.title}</p>
                  <span className="badge blue">{p.team}</span>
                  <div>
                    <Mail size={14} />
                    {p.email}
                  </div>
                </Link>
              ))}
            </div>
            {!data.results.length && <Empty title="No people found" />}
            <Pager next={data.next} onNext={setCursor} />
          </>
        )}
      </Resource>
    </>
  );
}
export function PersonDetail() {
  const { id } = useParams();
  const query = useResource<Person>(`/profiles/${id}`);
  return (
    <Resource query={query}>
      {(p) => (
        <>
          <Link className="back-link" to="/people">
            ← People directory
          </Link>
          <PageHeader title={p.name} description={`${p.title} · ${p.team}`} />
          <section className="panel detail-panel profile-detail">
            <Avatar name={p.name} />
            <h2>Work profile</h2>
            <dl>
              <dt>Work email</dt>
              <dd>
                <a href={`mailto:${p.email}`}>{p.email}</a>
              </dd>
              <dt>Job title</dt>
              <dd>{p.title}</dd>
              <dt>Directory team</dt>
              <dd>{p.team}</dd>
            </dl>
            {p.bio && <p className="prose">{p.bio}</p>}
          </section>
        </>
      )}
    </Resource>
  );
}
type Personal = { phone: string; address: string; emergency_contact: string };
function PersonalForm() {
  const session = useSession();
  const query = useResource<Personal>(`/profiles/${session.id}/personal`);
  const save = useMutation({
    mutationFn: (values: Personal) =>
      api(`/profiles/${session.id}/personal`, "PATCH", values),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: [`/profiles/${session.id}/personal`],
      }),
  });
  return (
    <Resource query={query}>
      {(p) => (
        <form
          onSubmit={(e: FormEvent<HTMLFormElement>) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget);
            save.mutate({
              phone: String(form.get("phone")),
              address: String(form.get("address")),
              emergency_contact: String(form.get("emergency_contact")),
            });
          }}
        >
          <div className="notice">
            <LockKeyhole size={18} /> Only you can access these fields. They are
            excluded from search and AI, even for you.
          </div>
          <Field label="Personal phone">
            <input
              type="tel"
              name="phone"
              maxLength={40}
              defaultValue={p.phone}
            />
          </Field>
          <Field label="Address">
            <textarea
              name="address"
              maxLength={1000}
              defaultValue={p.address}
            />
          </Field>
          <Field label="Emergency contact">
            <input
              name="emergency_contact"
              maxLength={300}
              defaultValue={p.emergency_contact}
            />
          </Field>
          {save.error && <ErrorNotice error={save.error} />}
          {save.isSuccess && (
            <p role="status" className="success-text">
              Personal details saved.
            </p>
          )}
          <button className="button" disabled={save.isPending}>
            Save personal details
          </button>
        </form>
      )}
    </Resource>
  );
}
export function Settings() {
  const session = useSession();
  const [tab, setTab] = useState("work");
  const [bio, setBio] = useState(session.bio || "");
  const save = useMutation({
    mutationFn: () => api(`/profiles/${session.id}`, "PATCH", { bio }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["session"] }),
  });
  return (
    <>
      <PageHeader
        eyebrow="MAKE IT YOURS"
        title="Account settings"
        description="Your profile and the details you choose to keep."
      />
      <div className="tabs settings-tabs">
        <button
          className={tab === "work" ? "active" : ""}
          onClick={() => setTab("work")}
        >
          Work profile
        </button>
        <button
          className={tab === "personal" ? "active" : ""}
          onClick={() => setTab("personal")}
        >
          Personal details · Only you
        </button>
      </div>
      <section className="panel detail-panel settings-panel">
        {tab === "personal" ? (
          <PersonalForm />
        ) : (
          <>
            <div className="profile-summary">
              <Avatar name={session.name} />
              <div>
                <h2>{session.name}</h2>
                <p>{session.email}</p>
              </div>
            </div>
            <div className="form-grid">
              <Field label="Job title">
                <input readOnly value={session.title} />
              </Field>
              <Field label="Directory team">
                <input readOnly value={session.team} />
              </Field>
            </div>
            <p className="fine">
              Your organization manages your name, email, role, and memberships.
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                save.mutate();
              }}
            >
              <Field
                label="About you"
                hint="Visible in your organization’s work directory."
              >
                <textarea
                  maxLength={1000}
                  rows={4}
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                />
              </Field>
              {save.error && <ErrorNotice error={save.error} />}
              {save.isSuccess && (
                <p className="success-text" role="status">
                  Profile saved.
                </p>
              )}
              <button className="button" disabled={save.isPending}>
                Save profile
              </button>
            </form>
          </>
        )}
      </section>
    </>
  );
}
