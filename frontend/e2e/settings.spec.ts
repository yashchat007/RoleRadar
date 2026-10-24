import { expect, test } from "@playwright/test";

test("settings theme and india-only controls sync with API", async ({ page }) => {
  let theme = "light";
  let indiaOnly = true;
  let digestEnabled = true;

  await page.route("**/api/v1/settings", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        json: { email: "dev@roleradar.local", theme, email_digest_enabled: digestEnabled },
      });
      return;
    }
    if (route.request().method() === "PATCH") {
      const body = route.request().postDataJSON() as { theme?: string; email_digest_enabled?: boolean };
      if (body.theme) theme = body.theme;
      if (body.email_digest_enabled !== undefined) digestEnabled = body.email_digest_enabled;
      await route.fulfill({
        json: { email: "dev@roleradar.local", theme, email_digest_enabled: digestEnabled },
      });
      return;
    }
    await route.continue();
  });

  await page.route("**/api/v1/profile", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        json: {
          skills: [],
          education: [],
          experience: [],
          projects: [],
          preferences: { india_only: indiaOnly, open_to_remote: true },
          updated_at: null,
        },
      });
      return;
    }
    if (route.request().method() === "PATCH") {
      const body = route.request().postDataJSON() as { preferences?: { india_only?: boolean } };
      if (body.preferences?.india_only !== undefined) {
        indiaOnly = body.preferences.india_only;
      }
      await route.fulfill({
        json: {
          skills: [],
          education: [],
          experience: [],
          projects: [],
          preferences: { india_only: indiaOnly, open_to_remote: true },
          updated_at: null,
        },
      });
      return;
    }
    await route.continue();
  });

  await page.route("**/api/v1/watches", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ json: [] });
      return;
    }
    await route.continue();
  });

  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();

  await page.getByRole("button", { name: "Dark" }).click();
  await expect.poll(() => page.evaluate(() => document.documentElement.getAttribute("data-theme"))).toBe(
    "dark",
  );
  await expect.poll(() => theme).toBe("dark");

  const indiaCheckbox = page.getByLabel("India-only roles (default)");
  await expect(indiaCheckbox).toBeChecked();
  await indiaCheckbox.uncheck();
  await expect.poll(() => indiaOnly).toBe(false);

  let jobsIndiaParam: string | null = null;
  await page.route("**/api/v1/jobs**", async (route) => {
    const url = new URL(route.request().url());
    jobsIndiaParam = url.searchParams.get("india_only");
    await route.fulfill({
      json: {
        items: [],
        meta: {
          total: 0,
          matching_total: 0,
          page: 1,
          page_size: 10,
          total_pages: 0,
          hidden_ineligible_count: 0,
        },
      },
    });
  });
  await page.route("**/api/v1/companies/discover", async (route) => {
    await route.fulfill({ json: [] });
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Discover" })).toBeVisible();
  await expect.poll(() => jobsIndiaParam).toBe("false");
});

test("test digest shows SMTP error from API", async ({ page }) => {
  await page.route("**/api/v1/settings", async (route) => {
    await route.fulfill({
      json: { email: "dev@roleradar.local", theme: "light", email_digest_enabled: true },
    });
  });
  await page.route("**/api/v1/profile", async (route) => {
    await route.fulfill({
      json: {
        skills: [],
        education: [],
        experience: [],
        projects: [],
        preferences: { india_only: true },
        updated_at: null,
      },
    });
  });
  await page.route("**/api/v1/watches", async (route) => {
    await route.fulfill({ json: [] });
  });
  await page.route("**/api/v1/digest/send", async (route) => {
    await route.fulfill({
      status: 503,
      json: { detail: "Connection refused" },
    });
  });

  await page.goto("/settings");
  await page.getByRole("button", { name: "Send test digest now" }).click();
  await expect(page.getByRole("alert")).toContainText("Connection refused");
});
