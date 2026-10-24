import { expect, test } from "@playwright/test";

const mockJobs = {
  items: [
    {
      id: "11111111-1111-1111-1111-111111111111",
      company_id: "22222222-2222-2222-2222-222222222222",
      company_name: "Stripe",
      title: "AI Engineer",
      location: "Remote",
      listing_url: "https://stripe.com/careers/listing/ai-engineer/1",
      apply_url: "https://stripe.com/careers/listing/ai-engineer/1",
      score: 82,
      eligible: true,
      top_reason: "Skills overlap: Python",
      company_logo_url: "https://www.google.com/s2/favicons?domain=stripe.com&sz=128",
      eligibility_label: "Eligible",
    },
  ],
  meta: {
    total: 1,
    matching_total: 1,
    page: 1,
    page_size: 10,
    total_pages: 1,
    hidden_ineligible_count: 0,
    sort_label: "Sorted by best match",
  },
};

const mockJob = {
  id: mockJobs.items[0].id,
  company_id: mockJobs.items[0].company_id,
  company_name: "Stripe",
  title: "AI Engineer",
  location: "Remote",
  listing_url: mockJobs.items[0].listing_url,
  apply_url: mockJobs.items[0].apply_url,
  listing_status: "active",
  description_sections: { summary: "Build AI systems" },
  last_seen_at: new Date().toISOString(),
};

const mockMatch = {
  job_id: mockJobs.items[0].id,
  score: 82,
  eligible: true,
  eligibility_reasons: [],
  factors: [{ name: "Skills", weight: 0.35, score: 90, evidence: ["Python"] }],
  requirements: [{ text: "Python experience", status: "met", evidence: "Python on resume" }],
  gaps: [],
  top_reasons: ["Skills overlap: Python"],
  computed_at: new Date().toISOString(),
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/jobs*", async (route) => {
    if (route.request().method() === "GET" && !route.request().url().includes("/match")) {
      if (route.request().url().includes(mockJob.id)) {
        await route.fulfill({ json: mockJob });
        return;
      }
      await route.fulfill({ json: mockJobs });
      return;
    }
    await route.continue();
  });
  await page.route(`**/api/v1/jobs/${mockJob.id}/match`, (route) =>
    route.fulfill({ json: mockMatch }),
  );
  await page.route(`**/api/v1/jobs/${mockJob.id}`, (route) => route.fulfill({ json: mockJob }));
  await page.route("**/api/v1/discovery/status", (route) =>
    route.fulfill({ json: { enabled_companies: 1, pending_validation: 20, scanning: false } }),
  );
  await page.route("**/api/v1/companies/discover", (route) =>
    route.fulfill({
      json: [
        {
          id: "22222222-2222-2222-2222-222222222222",
          name: "Stripe",
          career_page_url: "https://stripe.com/jobs/search",
          parser_status: "enabled",
          is_enabled: true,
          last_scan_status: "success",
          active_job_count: 1,
          source_state: "scan_ok",
          company_logo_url: "https://www.google.com/s2/favicons?domain=stripe.com&sz=128",
          priority_rank: 11,
        },
      ],
    }),
  );
  await page.route("**/api/v1/settings", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({ json: { email: "dev@roleradar.local", theme: "light", email_digest_enabled: true } });
    }
    return route.continue();
  });
});

test("discover row opens detail pane", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Discover" })).toBeVisible();
  await page.getByText("AI Engineer", { exact: true }).click();
  await expect(page.getByTestId("job-detail-pane")).toContainText("AI Engineer");
  await expect(page.getByTestId("job-detail-pane")).toContainText(/Resume match|Upload a resume to calculate your match/);
  await expect(page.getByTestId("job-detail-pane").getByText("Eligible")).toBeVisible();
});
