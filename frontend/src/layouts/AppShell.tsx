import { NavLink, Outlet } from "react-router-dom";
import { Bookmark, Compass, Settings, User } from "lucide-react";
import { cn } from "../lib/cn";

const nav = [
  { to: "/", label: "Discover", icon: Compass },
  { to: "/saved", label: "Saved", icon: Bookmark },
  { to: "/profile", label: "Profile", icon: User },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell() {
  return (
    <div className="min-h-screen bg-[var(--color-canvas)] text-[var(--color-text-primary)] pb-16 md:pb-0">
      <div className="mx-auto flex max-w-[1200px] min-h-screen">
        <aside
          className="hidden md:flex w-[200px] shrink-0 flex-col border-r border-[var(--color-border-subtle)] bg-[var(--color-surface)] px-3 py-5"
          aria-label="Main"
        >
          <div className="px-2 pb-6">
            <span className="text-subheading font-medium">RoleRadar</span>
          </div>
          <nav className="flex flex-col gap-0.5">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex h-10 items-center gap-2 rounded-[var(--radius-sm)] px-3 text-label text-[var(--color-text-secondary)] hover:bg-[var(--color-sunken)]",
                    isActive && "font-medium text-[var(--color-text-primary)] bg-[var(--color-sunken)]",
                  )
                }
              >
                <item.icon size={18} strokeWidth={1.5} aria-hidden="true" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main id="main-content" className="flex-1 px-4 py-5 md:px-8 min-w-0" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
      <nav
        className="md:hidden fixed bottom-0 inset-x-0 flex border-t border-[var(--color-border-subtle)] bg-[var(--color-surface)]"
        aria-label="Mobile"
      >
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "flex-1 flex flex-col items-center justify-center gap-0.5 py-2.5 text-caption",
                isActive ? "text-[var(--color-brand)]" : "text-[var(--color-text-secondary)]",
              )
            }
          >
            <item.icon size={20} strokeWidth={1.5} />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
