import { describe, it, expect } from "vitest";
import { demoRequest } from "./demo";
import type { Update, Conversation, Document } from "../../types";
describe("synthetic interaction model", () => {
  it("creates private drafts and preserves published revisions", async () => {
    const u = await demoRequest<Update>("/updates", "POST", {
      body: "Synthetic work completed",
      work_date: "2026-10-04",
    });
    expect(u.visibility).toBe("private");
    expect(u.status).toBe("draft");
    const published = await demoRequest<Update>(
      `/updates/${u.id}/publish`,
      "POST",
      { visibility: "lead_visible", version: u.version },
    );
    const edited = await demoRequest<Update>(`/updates/${u.id}`, "PATCH", {
      body: "Revised synthetic update",
      version: published.version,
    });
    expect(edited.revisions[0].body).toBe("Synthetic work completed");
    await expect(
      demoRequest(`/updates/${u.id}`, "PATCH", {
        body: "Stale edit",
        version: 1,
      }),
    ).rejects.toThrow("This item changed");
  });
  it("never exposes personal fields through another profile", async () => {
    await expect(demoRequest("/profiles/dev/personal")).rejects.toThrow(
      "This page is unavailable",
    );
  });
  it("hides saved answers and source titles after the source becomes unavailable", async () => {
    const c = await demoRequest<Conversation>("/conversations", "POST");
    const answered = await demoRequest<Conversation>(
      `/conversations/${c.id}/messages`,
      "POST",
      { question: "What is Atlas?" },
    );
    expect(answered.messages[0].citations).toHaveLength(1);
    const d = await demoRequest<Document>("/documents/d1");
    await demoRequest("/documents/d1/access", "PATCH", {
      classification: "restricted",
      grants: ["asha"],
      version: d.version,
    });
    const reopened = await demoRequest<Conversation>(`/conversations/${c.id}`);
    expect(reopened.messages[0].state).toBe("access_changed");
    expect(reopened.messages[0].answer).toBeUndefined();
    expect(reopened.messages[0].citations).toEqual([]);
  });
});
