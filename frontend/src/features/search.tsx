import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search as SearchIcon, ArrowUpRight, Bell } from "lucide-react";
import { api } from "../services/api";
import {
  Badge,
  Empty,
  PageHeader,
  Resource,
  Pager,
  useResource,
} from "../components/ui";
import type { List, SearchResult } from "../types";
export function Search() {
  const [params, setParams] = useSearchParams();
  const term = params.get("q") || "";
  const [q, setQ] = useState(term);
  const [cursor, setCursor] = useState("");
  const query = useQuery({
    queryKey: ["search", term, cursor],
    queryFn: () =>
      api<List<SearchResult>>("/search", "POST", { query: term, cursor }),
    enabled: !!term,
  });
  function submit(e: FormEvent) {
    e.preventDefault();
    setCursor("");
    setParams({ q: q.trim() });
  }
  return (
    <>
      <PageHeader
        eyebrow="FIND YOUR CONTEXT"
        title="Search your workspace"
        description="Documents, work updates, and people you can access."
      />
      <form onSubmit={submit} className="toolbar">
        <label className="search-input wide">
          <SearchIcon size={18} />
          <input
            aria-label="Search query"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="What are you looking for?"
            maxLength={300}
          />
        </label>
        <button className="button">Search</button>
      </form>
      {term ? (
        <Resource query={query}>
          {(data) => (
            <>
              <section className="panel">
                {data.results.map((r) => (
                  <Link
                    key={`${r.type}-${r.id}`}
                    className="search-result"
                    to={`/${r.type === "document" ? "documents" : r.type === "update" ? "work" : "people"}/${r.id}`}
                  >
                    <div>
                      <Badge tone="blue">{r.type}</Badge>
                      <h2>{r.title}</h2>
                      <p>{r.snippet}</p>
                    </div>
                    <ArrowUpRight size={19} />
                  </Link>
                ))}
                {!data.results.length && (
                  <Empty title="No results found">
                    Try another phrase or a more specific question.
                  </Empty>
                )}
              </section>
              <Pager next={data.next} onNext={setCursor} />
            </>
          )}
        </Resource>
      ) : (
        <Empty title="What would you like to find?">
          Search for a project document, work update, or colleague.
        </Empty>
      )}
    </>
  );
}
export function Notifications() {
  const query =
    useResource<List<{ id: string; message: string; date: string }>>(
      "/notifications",
    );
  return (
    <>
      <PageHeader
        title="Notifications"
        description="The latest from your workspace."
      />
      <section className="panel">
        <Resource query={query}>
          {(data) =>
            data.results.length ? (
              data.results.map((n) => (
                <div className="list-row" key={n.id}>
                  <Bell size={19} />
                  <p>{n.message}</p>
                  <small>{n.date}</small>
                </div>
              ))
            ) : (
              <Empty title="You’re all caught up">
                Your workspace notifications will appear here.
              </Empty>
            )
          }
        </Resource>
      </section>
    </>
  );
}
