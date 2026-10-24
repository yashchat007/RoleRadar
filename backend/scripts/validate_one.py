import asyncio
import sys
from sqlalchemy import select
from app.database import SessionLocal
from app.discovery.validation import validate_company_adapter
from app.models.company import Company
from app.services.seed import seed_companies, sync_pilot_adapter_keys

async def main(name: str) -> None:
    async with SessionLocal() as s:
        await seed_companies(s)
        await sync_pilot_adapter_keys(s)
        c = await s.scalar(select(Company).where(Company.name == name))
        if not c:
            print("not found", name)
            return
        r = await validate_company_adapter(s, c)
        await s.refresh(c)
        print(name, "passed=", r.passed, "sampled=", r.jobs_sampled, "enabled=", c.is_enabled, "err=", c.last_error)

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
