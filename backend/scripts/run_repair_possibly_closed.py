import asyncio
import json

from app.database import SessionLocal
from app.services.repair_possibly_closed import repair_incorrect_possibly_closed


async def main() -> None:
    async with SessionLocal() as session:
        repairs = await repair_incorrect_possibly_closed(session)
        await session.commit()
        print(json.dumps({"repaired": len(repairs), "items": repairs}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
