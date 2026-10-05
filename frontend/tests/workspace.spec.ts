import { test, expect } from "@playwright/test";
test("dashboard and responsive navigation", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Welcome back, Asha" }),
  ).toBeVisible();
  await expect(
    page.getByText("Synthetic demo · Changes reset on refresh"),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Organization", exact: true }),
  ).toHaveCount(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `test-results/dashboard-${test.info().project.name}.png`,
    fullPage: true,
  });
  if (test.info().project.name === "mobile") {
    await expect(
      page.getByRole("navigation", { name: "Main navigation" }),
    ).toHaveCount(0);
    await page.getByRole("button", { name: "Open navigation" }).click();
    await expect(
      page.getByRole("navigation", { name: "Main navigation" }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("button", { name: "Open navigation" }),
    ).toBeFocused();
  }
});
test("create, edit and publish an update with explicit visibility", async ({
  page,
}) => {
  await page.goto("/work");
  await page.getByRole("button", { name: "New update", exact: true }).click();
  await page
    .getByRole("textbox", { name: "What did you work on?" })
    .fill("Finished the synthetic integration tests for Atlas.");
  await page.getByRole("button", { name: "Save private draft" }).click();
  await expect(page.getByText("Only you can read this update.")).toBeVisible();
  await page.getByRole("button", { name: "Publish update" }).click();
  await page
    .getByLabel("Who can read this update?")
    .selectOption("lead_visible");
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(
    page.getByText(
      "You and your current team lead can read this published update.",
    ),
  ).toBeVisible();
  await page.getByRole("button", { name: "Edit update" }).click();
  await page
    .getByRole("textbox", { name: "What did you work on?" })
    .fill("Finished integration tests and recorded synthetic results.");
  await page.getByRole("button", { name: "Save revision" }).click();
  await expect(
    page.getByRole("heading", { name: "Revision history" }),
  ).toBeVisible();
});
test("upload and publish a restricted synthetic document", async ({ page }) => {
  await page.goto("/documents");
  await page
    .getByRole("button", { name: "Upload document", exact: true })
    .click();
  await page.getByLabel("Document title").fill("Synthetic test guide");
  await page.getByLabel("Document file").setInputFiles({
    name: "guide.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Synthetic testing guidance only."),
  });
  await page.getByRole("button", { name: "Upload to private staging" }).click();
  await page.getByRole("link", { name: /^Synthetic test guide/ }).click();
  await page.getByRole("button", { name: "Publish document" }).click();
  await expect(page.getByRole("checkbox", { name: /Asha Rao/ })).toBeChecked();
  await page.getByRole("button", { name: "Confirm and publish" }).click();
  await expect(
    page.getByRole("button", { name: "Download", exact: true }),
  ).toBeEnabled();
});
test("AI answers cite sources, and unavailable routes stay generic", async ({
  page,
}) => {
  await page.goto("/assistant");
  await page.getByLabel("Ask your workspace").fill("What is Atlas working on?");
  await page.getByRole("button", { name: "Send question" }).click();
  await expect(
    page.getByText(/This is a fixed synthetic example/),
  ).toBeVisible();
  await page.getByRole("link", { name: /Atlas · Project overview/ }).click();
  await expect(
    page.getByRole("heading", { name: "Atlas · Project overview", level: 1 }),
  ).toBeVisible();
  await page.goto("/documents/unknown");
  await expect(page.getByRole("alert")).toHaveText(
    /This page is unavailable or you no longer have access/,
  );
});
test("personal fields are isolated and sign-out clears the workspace", async ({
  page,
}) => {
  await page.goto("/settings");
  await page
    .getByRole("button", { name: "Personal details · Only you" })
    .click();
  await page.getByLabel("Personal phone").fill("555-0100");
  await page.getByRole("button", { name: "Save personal details" }).click();
  await expect(page.getByText("Personal details saved.")).toBeVisible();
  await page
    .getByRole("textbox", { name: "Search workspace" })
    .fill("555-0100");
  await page.getByRole("textbox", { name: "Search workspace" }).press("Enter");
  await expect(
    page.getByRole("heading", { name: "No results found" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome to your workspace" }),
  ).toBeVisible();
  await expect(page.getByLabel("Personal phone")).toHaveCount(0);
});

test("saved answers hide content after a source changes", async ({ page }) => {
  await page.goto("/assistant");
  await page.getByLabel("Ask your workspace").fill("Summarize Atlas");
  await page.getByRole("button", { name: "Send question" }).click();
  await page.getByRole("link", { name: /Atlas · Project overview/ }).click();
  await page.getByRole("button", { name: "Manage access" }).click();
  await page
    .getByRole("combobox", { name: "Classification", exact: true })
    .selectOption("restricted");
  await page.getByRole("checkbox", { name: /Asha Rao/ }).check();
  await page.getByRole("button", { name: "Save access", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.goBack();
  await expect(
    page.getByText(/Access to this answer has changed/),
  ).toBeVisible();
  await expect(page.getByText(/This is a fixed synthetic example/)).toHaveCount(
    0,
  );
  await expect(
    page.getByRole("link", { name: /Atlas · Project overview/ }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Regenerate from current sources" })
    .click();
  await expect(
    page.getByText(
      "I couldn’t find enough information in your accessible sources to answer that question.",
    ),
  ).toBeVisible();
});

test("directory, project, search, and administration routes respect employee scope", async ({
  page,
}) => {
  await page.goto("/projects/atlas");
  await expect(
    page.getByRole("heading", { name: "Atlas", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: /Dev Shah/ }).click();
  await expect(
    page.getByRole("heading", { name: "Dev Shah", exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("Personal phone")).toHaveCount(0);
  await page.goto("/search?q=Atlas");
  await expect(
    page.getByRole("heading", { name: "Atlas · Project overview" }),
  ).toBeVisible();
  await page.goto("/admin/users");
  await expect(
    page.getByRole("heading", { name: "Page unavailable" }),
  ).toBeVisible();
});
