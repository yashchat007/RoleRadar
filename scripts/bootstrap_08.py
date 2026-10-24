import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def w(rel, content):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

w("frontend/src/layouts/AppShell.tsx", """import { NavLink, Outlet } from "react-router-dom";
import { Calendar, Bookmark, Compass, LayoutDashboard, Settings, User } from "lucide-react";
import { cn } from "../lib/cn";

const nav = [
  { to: "/", label: "Today", icon: LayoutDashboard },
  { to: "/discover", label: "Discover", icon: Compass },
  { to: "/tracker", label: "Tracker", icon: Calendar },
  { to: "/saved", label: "Saved", icon: Bookmark },
  { to: "/profile", label: "Profile", icon: User },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell() {
  return (
    <div className="min-h-screen bg-[var(--color-canvas)] text-[var(--color-text-primary)]">
      <div className="mx-auto flex max-w-[1280px] min-h-screen">
        <aside
          className="hidden md:flex w-[var(--sidebar-width)] shrink-0 flex-col border-r border-[var(--color-border-subtle)] bg-[var(--color-surface)] px-3 py-4"
          aria-label="Main"
        >
          <div className="px-2 pb-4">
            <span className="text-subheading">RoleRadar</span>
            <p className="text-caption text-[var(--color-text-tertiary)]">Research desk</p>
          </div>
          <nav className="flex flex-col gap-1">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex h-9 items-center gap-2 rounded-[var(--radius-sm)] px-2 text-label text-[var(--color-text-secondary)] hover:bg-[var(--color-sunken)]",
                    isActive && "border-l-2 border-[var(--color-brand)] font-medium text-[var(--color-text-primary)] bg-[var(--color-brand-tint)]",
                  )
                }
              >
                <item.icon size={20} strokeWidth={1.5} aria-hidden="true" />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <p className="mt-auto px-2 pt-4 text-caption text-[var(--color-text-tertiary)]">Scanning 0 companies…</p>
        </aside>
        <main className="flex-1 px-4 py-6 md:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
""")

w("frontend/src/pages/TodayPage.tsx", """export function TodayPage() {
  return (
    <div>
      <h1 className="text-display">Morning briefing</h1>
      <p className="mt-2 text-[var(--color-text-secondary)]">Connect discovery to see ranked matches and source health.</p>
    </div>
  );
}
""")

w("frontend/src/pages/PlaceholderPage.tsx", """export function PlaceholderPage({ title }: { title: string }) {
  return (
    <div>
      <h1 className="text-heading">{title}</h1>
      <p className="mt-2 text-[var(--color-text-secondary)]">Coming in the next implementation phase.</p>
    </div>
  );
}
""")

w("frontend/src/pages/DesignSystemPage.tsx", """import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Field, Input } from "../components/ui/Input";
import { ScoreBar } from "../components/ui/ScoreBar";

export function DesignSystemPage() {
  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-display">Research desk design system</h1>
        <p className="mt-2 text-[var(--color-text-secondary)]">Warm paper, ink type, plum accents. Scores use ink and plum — never red-to-green.</p>
      </div>
      <section className="space-y-3">
        <h2 className="text-subheading">Typography</h2>
        <p className="text-title">Newsreader title</p>
        <p className="text-body">IBM Plex Sans body at 14/22.</p>
        <p className="font-mono font-tabular text-label">REQ-10482 · 82</p>
      </section>
      <section className="space-y-3">
        <h2 className="text-subheading">Buttons</h2>
        <div className="flex flex-wrap gap-2">
          <Button>Primary action</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="quiet">Quiet</Button>
        </div>
      </section>
      <section className="space-y-3">
        <h2 className="text-subheading">Badges and score</h2>
        <div className="flex flex-wrap gap-2">
          <Badge tone="ochre">New since yesterday</Badge>
          <Badge tone="success">Met requirement</Badge>
          <Badge tone="warning">Closing soon</Badge>
        </div>
        <ScoreBar score={82} />
      </section>
      <section className="space-y-3">
        <h2 className="text-subheading">Form</h2>
        <Field label="Role search" help="Opened with / on Discover.">
          <Input name="demo" />
        </Field>
      </section>
    </div>
  );
}
""")

w("frontend/src/App.tsx", """import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./layouts/AppShell";
import { DesignSystemPage } from "./pages/DesignSystemPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { TodayPage } from "./pages/TodayPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<TodayPage />} />
          <Route path="discover" element={<PlaceholderPage title="Discover" />} />
          <Route path="tracker" element={<PlaceholderPage title="Tracker" />} />
          <Route path="saved" element={<PlaceholderPage title="Saved" />} />
          <Route path="profile" element={<PlaceholderPage title="Profile" />} />
          <Route path="settings" element={<PlaceholderPage title="Settings" />} />
        </Route>
        <Route path="design-system" element={<DesignSystemPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
""")

w("frontend/src/main.tsx", """import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/newsreader/500.css";
import "@fontsource/ibm-plex-mono/400.css";
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
""")

w("frontend/index.html", """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>RoleRadar</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""")

print("app shell ok")
