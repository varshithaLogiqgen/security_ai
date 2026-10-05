import { afterEach, describe, expect, it, vi } from "vitest";
import { request } from "./client";
afterEach(() => vi.unstubAllGlobals());
describe("API boundary", () => {
  it("uses session cookies, no-store, CSRF, and never a client identity header", async () => {
    document.cookie = "csrftoken=example";
    const fetch = vi
      .fn()
      .mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetch);
    await request("/updates", { method: "POST", body: "{}" });
    expect(fetch).toHaveBeenCalledWith(
      "/api/v1/updates",
      expect.objectContaining({
        credentials: "include",
        cache: "no-store",
        headers: expect.objectContaining({ "X-CSRFToken": "example" }),
      }),
    );
  });
  it("treats inaccessible and missing resources identically", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response("{}", { status: 403 }))
        .mockResolvedValueOnce(new Response("{}", { status: 404 })),
    );
    await expect(request("/documents/secret")).rejects.toThrow(
      "This page is unavailable or you no longer have access.",
    );
    await expect(request("/documents/missing")).rejects.toThrow(
      "This page is unavailable or you no longer have access.",
    );
  });
  it("expires the session on 401 without surfacing backend response content", async () => {
    const expired = vi.fn();
    window.addEventListener("session-expired", expired);
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response("private backend details", { status: 401 }),
        ),
    );
    await expect(request("/me")).rejects.toThrow("Your session has expired");
    expect(expired).toHaveBeenCalledOnce();
    window.removeEventListener("session-expired", expired);
  });
  it("does not silently retry version conflicts", async () => {
    const fetch = vi.fn().mockResolvedValue(new Response("", { status: 409 }));
    vi.stubGlobal("fetch", fetch);
    await expect(request("/updates/u1", { method: "PATCH" })).rejects.toThrow(
      "This item changed",
    );
    expect(fetch).toHaveBeenCalledOnce();
  });
});
