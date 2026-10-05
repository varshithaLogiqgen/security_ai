import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { demoMode } from "../services/api/client";
import { queryClient } from "./queryClient";
import { Loading, ErrorNotice } from "../components/ui";
import { ShieldCheck, ArrowRight, LockKeyhole } from "lucide-react";
import type { Session } from "../types";
const SessionContext = createContext<Session | null>(null);
export function useSession() {
  return useContext(SessionContext)!;
}
export function SessionProvider({ children }: { children: ReactNode }) {
  const [expired, setExpired] = useState(false);
  const [demoSignedIn, setDemoSignedIn] = useState(true);
  const session = useQuery({
    queryKey: ["session"],
    queryFn: () => api<Session>("/me"),
    enabled: !expired && demoSignedIn,
  });
  useEffect(() => {
    const reset = () => {
      setExpired(true);
      void queryClient.cancelQueries();
      queryClient.clear();
    };
    window.addEventListener("session-expired", reset);
    const logout = () => {
      setDemoSignedIn(false);
      reset();
    };
    window.addEventListener("signed-out", logout);
    return () => {
      window.removeEventListener("session-expired", reset);
      window.removeEventListener("signed-out", logout);
    };
  }, []);
  if (session.isLoading) return <Loading />;
  if (expired || !demoSignedIn || !session.data || session.error)
    return (
      <div className="login">
        <div className="login-brand">
          <ShieldCheck size={44} />
          <h1>
            A little less searching.
            <br />A lot more clarity.
          </h1>
          <p>
            Your work, your team, and the knowledge you need.
            <br />
            Together in one protected workspace.
          </p>
          <div className="login-footer">
            SECUREAI · YOUR KNOWLEDGE, CONNECTED
          </div>
        </div>
        <section className="login-form">
          <div className="brand">
            <ShieldCheck /> SecureAI
          </div>
          <h2>Welcome to your workspace</h2>
          <p>Sign in with your organization account to continue.</p>
          {expired && (
            <div className="notice">
              Your session has ended. Sign in to continue.
            </div>
          )}
          {session.error && !expired && <ErrorNotice error={session.error} />}
          <button
            className="button"
            onClick={() => {
              if (demoMode) {
                setExpired(false);
                setDemoSignedIn(true);
                void session.refetch();
              } else
                window.location.assign(
                  `${import.meta.env.VITE_API_BASE_URL || "/api/v1"}/auth/login`,
                );
            }}
          >
            {demoMode
              ? "Enter synthetic demo"
              : "Continue with organization SSO"}
            <ArrowRight size={17} />
          </button>
          <p className="fine">
            <LockKeyhole size={14} /> Authentication and account recovery are
            managed by your organization.
          </p>
        </section>
      </div>
    );
  return (
    <SessionContext.Provider value={session.data}>
      {children}
    </SessionContext.Provider>
  );
}
