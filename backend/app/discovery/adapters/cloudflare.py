from app.discovery.adapters.base import OfficialSiteAdapter
from app.discovery.context import ScanContext
from app.discovery.types import AdapterResult, InspectionReport


class CloudflareOfficialAdapter(OfficialSiteAdapter):
    adapter_key = "cloudflare_official"
    official_hosts = frozenset({"www.cloudflare.com", "cloudflare.com"})

    async def inspect(self, ctx: ScanContext) -> InspectionReport:
        return InspectionReport(
            extraction_mode="browser_render",
            allowed_hosts=list(self.official_hosts),
            notes=(
                "Careers index is on cloudflare.com but open roles link out to boards.greenhouse.io only. "
                "RoleRadar requires apply/listing URLs on the official careers domain."
            ),
        )

    async def extract_listings(self, ctx: ScanContext) -> AdapterResult:
        if ctx.page is None:
            return AdapterResult(fatal_error="Browser page required for Cloudflare inspection")

        page = ctx.page
        await page.goto(
            "https://www.cloudflare.com/careers/jobs/",
            wait_until="domcontentloaded",
            timeout=90_000,
        )
        await page.wait_for_timeout(4000)
        hrefs = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        official = [h for h in hrefs if "cloudflare.com/careers" in h and "/jobs/" not in h.rstrip("/") + "/"]
        greenhouse = [h for h in hrefs if "boards.greenhouse.io" in h]

        if official:
            return AdapterResult(
                warnings=["Cloudflare official detail URLs detected but parser not implemented yet"],
                fatal_error=None,
            )

        return AdapterResult(
            fatal_error=(
                "Cloudflare careers page exposes listings only via boards.greenhouse.io links "
                f"({len(set(greenhouse))} found). Cannot ingest without official cloudflare.com job URLs."
            )
        )
