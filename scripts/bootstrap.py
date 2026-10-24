import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def w(rel, content):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

w("docker-compose.yml", """services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: roleradar
      POSTGRES_PASSWORD: roleradar
      POSTGRES_DB: roleradar
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
""")

w("backend/app/config.py", """from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://roleradar:roleradar@127.0.0.1:5432/roleradar"
    cors_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    discovery_blocklist_hosts: list[str] = [
        "boards-api.greenhouse.io",
        "api.lever.co",
        "jobs.ashbyhq.com",
        "api.ashbyhq.com",
    ]


settings = Settings()
""")

print("bootstrap part 1 ok")
