import fs from "fs";
import path from "path";
const root = process.cwd();
function w(rel, content) {
  const p = path.join(root, rel);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content, "utf8");
}
w("backend/requirements.txt", "fastapi>=0.115.0\nuvicorn[standard]>=0.32.0\nsqlalchemy[asyncio]>=2.0.36\nasyncpg>=0.30.0\nalembic>=1.14.0\npydantic-settings>=2.6.0\nhttpx>=0.28.0\npython-multipart>=0.0.18\napscheduler>=3.10.4\n");
console.log("ok");
