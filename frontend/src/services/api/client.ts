export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export const demoMode = import.meta.env.VITE_DEMO_MODE === "true";
const base = import.meta.env.VITE_API_BASE_URL || "/api/v1";
export function csrfToken() {
  return (
    document.cookie
      .split("; ")
      .find((c) => c.startsWith("csrftoken="))
      ?.slice(10) || ""
  );
}
export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...options,
    credentials: "include",
    cache: "no-store",
    headers: {
      ...(options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      "X-CSRFToken": decodeURIComponent(csrfToken()),
      ...options.headers,
    },
  });
  if (!response.ok) {
    if (response.status === 401)
      window.dispatchEvent(new Event("session-expired"));
    throw new ApiError(
      response.status,
      response.status === 401
        ? "Your session has expired. Please sign in again."
        : [403, 404].includes(response.status)
          ? "This page is unavailable or you no longer have access."
          : response.status === 409
            ? "This item changed. Reload the page before saving again."
            : response.status === 429
              ? "Too many requests. Please try again shortly."
              : "We couldn’t complete that request. Please try again.",
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
export async function downloadFile(id: string) {
  const response = await fetch(
    `${base}/documents/${encodeURIComponent(id)}/download`,
    { credentials: "include", cache: "no-store" },
  );
  if (!response.ok) {
    if (response.status === 401)
      window.dispatchEvent(new Event("session-expired"));
    throw new ApiError(
      response.status,
      "This file is unavailable or you no longer have access.",
    );
  }
  return response.blob();
}
