import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import {
  Sparkles,
  Plus,
  ArrowUp,
  MessageSquare,
  FileText,
  ShieldCheck,
  Trash2,
  ArrowUpRight,
} from "lucide-react";
import { api } from "../services/api";
import { queryClient } from "../app/queryClient";
import {
  Avatar,
  ErrorNotice,
  Resource,
  useResource,
  Modal,
} from "../components/ui";
import { useSession } from "../app/session";
import type { Conversation, List, Message } from "../types";
function Answer({
  message,
  onRegenerate,
}: {
  message: Message;
  onRegenerate: () => void;
}) {
  return (
    <article className="answer">
      <span className="spark-icon">
        <Sparkles size={19} />
      </span>
      <div>
        <strong>
          SecureAI <span className="muted">· Your knowledge assistant</span>
        </strong>
        {message.state === "access_changed" ? (
          <div className="notice">
            Access to this answer has changed. Its answer and sources are
            hidden.
            <button className="text-button" onClick={onRegenerate}>
              Regenerate from current sources
            </button>
          </div>
        ) : (
          <>
            <p className="prose">{message.answer}</p>
            {message.citations.length > 0 && (
              <>
                <p className="citation-label">SOURCES</p>
                <div className="citations">
                  {message.citations.map((c, i) => (
                    <Link
                      key={c.id}
                      to={`/${c.source_type === "document" ? "documents" : c.source_type === "update" ? "work" : "people"}/${encodeURIComponent(c.source_id)}`}
                    >
                      <span>{i + 1}</span>
                      <FileText size={16} />
                      <div>
                        <strong>{c.title}</strong>
                        <small>
                          v{c.version} · {c.locator}
                        </small>
                      </div>
                      <ArrowUpRight size={14} />
                    </Link>
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </article>
  );
}
export function Assistant() {
  const { id } = useParams();
  const session = useSession();
  const navigate = useNavigate();
  const history = useResource<List<Conversation>>("/conversations");
  const [question, setQuestion] = useState("");
  const [deleteDialog, setDeleteDialog] = useState(false);
  const send = useMutation({
    mutationFn: async (q: string) => {
      const conversation = id
        ? { id }
        : await api<Conversation>("/conversations", "POST");
      return api<Conversation>(
        `/conversations/${conversation.id}/messages`,
        "POST",
        { question: q },
      );
    },
    onSuccess: async (conversation) => {
      setQuestion("");
      await queryClient.invalidateQueries();
      navigate(`/assistant/${conversation.id}`);
    },
  });
  const remove = useMutation({
    mutationFn: () => api(`/conversations/${id}`, "DELETE"),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      setDeleteDialog(false);
      navigate("/assistant");
    },
  });
  function submit(e: FormEvent) {
    e.preventDefault();
    if (question.trim() && !send.isPending) send.mutate(question.trim());
  }
  return (
    <div className="assistant-layout">
      <aside className="chat-sidebar">
        <div className="spread">
          <h2>Conversations</h2>
          <Link
            className="icon-button"
            to="/assistant"
            aria-label="New conversation"
          >
            <Plus size={19} />
          </Link>
        </div>
        <Resource query={history}>
          {(data) => (
            <>
              {data.results.length === 0 ? (
                <p className="muted fine">
                  Your conversations will appear here.
                </p>
              ) : (
                data.results.map((c) => (
                  <Link
                    key={c.id}
                    className={`conversation-link ${id === c.id ? "selected" : ""}`}
                    to={`/assistant/${c.id}`}
                  >
                    <MessageSquare size={16} />
                    <span>{c.title}</span>
                  </Link>
                ))
              )}
            </>
          )}
        </Resource>
        <div className="chat-privacy">
          <ShieldCheck size={18} />
          <p>
            Just your knowledge.
            <br />
            Only your conversations.
          </p>
        </div>
      </aside>
      <section className="chat-main">
        <div className="chat-top">
          <span>
            <Sparkles size={18} /> SecureAI Assistant{" "}
            <span className="badge purple">Read-only</span>
          </span>
          {id && (
            <button
              className="icon-button"
              aria-label="Delete conversation"
              onClick={() => setDeleteDialog(true)}
            >
              <Trash2 size={17} />
            </button>
          )}
        </div>
        <div className="chat-content">
          {id ? (
            <ConversationView
              key={id}
              id={id}
              regenerate={(q) => send.mutate(q)}
            />
          ) : (
            <div className="assistant-empty">
              <div className="assistant-emblem">
                <Sparkles size={34} />
              </div>
              <p className="eyebrow">A CLEARER WAY TO WORK</p>
              <h1>
                Your next answer
                <br />
                starts with a question.
              </h1>
              <p>
                Bring your workspace knowledge together.
                <br />
                Get helpful answers with sources you can open.
              </p>
              <div className="suggestions">
                {[
                  "What is the Atlas project working on?",
                  "Summarize my recent work updates",
                  "Who works on the Payments team?",
                ].map((q) => (
                  <button onClick={() => setQuestion(q)} key={q}>
                    <MessageSquare size={17} />
                    {q}
                    <ArrowUpRight size={15} />
                  </button>
                ))}
              </div>
            </div>
          )}
          {send.isPending && (
            <div className="notice" role="status">
              <Sparkles size={18} /> Finding accessible sources and checking the
              answer…
            </div>
          )}
          {send.error && <ErrorNotice error={send.error} />}
        </div>
        <form className="chat-compose" onSubmit={submit}>
          <label className="sr-only" htmlFor="question">
            Ask your workspace
          </label>
          <textarea
            id="question"
            rows={2}
            placeholder="Ask a question about your workspace…"
            value={question}
            maxLength={4000}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={send.isPending}
          />
          <button
            className="button"
            aria-label="Send question"
            disabled={!question.trim() || send.isPending}
          >
            <ArrowUp size={20} />
          </button>
        </form>
        <p className="chat-disclaimer">
          <ShieldCheck size={12} /> Answers use accessible sources. Always check
          the citations.
        </p>
      </section>
      {deleteDialog && (
        <Modal
          title="Delete conversation?"
          onClose={() => setDeleteDialog(false)}
        >
          <p>This removes the conversation from your history.</p>
          {remove.error && <ErrorNotice error={remove.error} />}
          <div className="modal-footer">
            <button
              className="button secondary"
              onClick={() => setDeleteDialog(false)}
            >
              Cancel
            </button>
            <button
              className="button danger"
              disabled={remove.isPending}
              onClick={() => remove.mutate()}
            >
              Delete conversation
            </button>
          </div>
        </Modal>
      )}
      <span className="sr-only">Signed in as {session.name}</span>
    </div>
  );
}
function ConversationView({
  id,
  regenerate,
}: {
  id: string;
  regenerate: (q: string) => void;
}) {
  const session = useSession();
  const query = useResource<Conversation>(`/conversations/${id}`);
  return (
    <Resource query={query}>
      {(c) => (
        <>
          {c.messages.map((m) => (
            <div key={m.id} className="message-pair">
              <div className="question">
                <Avatar name={session.name} small />
                <div>
                  <strong>You</strong>
                  <p>{m.question}</p>
                </div>
              </div>
              <Answer message={m} onRegenerate={() => regenerate(m.question)} />
            </div>
          ))}
        </>
      )}
    </Resource>
  );
}
