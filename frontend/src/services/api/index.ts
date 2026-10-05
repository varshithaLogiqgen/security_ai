import { demoMode, request, downloadFile } from "./client";
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
  version?: number,
): Promise<T> {
  if (demoMode) {
    const { demoRequest } = await import("./demo");
    return demoRequest<T>(path, method, body);
  }
  return request<T>(path, {
    method,
    body:
      body instanceof FormData
        ? body
        : body === undefined
          ? undefined
          : JSON.stringify(body),
    headers: {
      ...(version === undefined ? {} : { "If-Match": String(version) }),
      ...(["POST", "PATCH"].includes(method)
        ? { "Idempotency-Key": crypto.randomUUID() }
        : {}),
    },
  });
}
export async function download(id: string) {
  return demoMode
    ? (await import("./demo")).demoDownload(id)
    : downloadFile(id);
}
