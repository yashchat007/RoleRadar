import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def w(rel, content):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

w("frontend/src/styles/tokens.css", """:root {
  --color-canvas: #f6f5f1;
  --color-surface: #ffffff;
  --color-sunken: #eeece6;
  --color-border-subtle: #e3e0d8;
  --color-border-strong: #c9c5ba;
  --color-text-primary: #1c1c19;
  --color-text-secondary: #55534c;
  --color-text-tertiary: #6e6b63;
  --color-action: #1c1c19;
  --color-action-hover: #33332e;
  --color-action-text: #ffffff;
  --color-brand: #6b2d5c;
  --color-brand-hover: #56234a;
  --color-brand-tint: #f3e8ef;
  --color-ochre: #9a5b13;
  --color-ochre-tint: #f7ecdd;
  --color-success: #2f6b3a;
  --color-success-bg: #e5efe6;
  --color-warning: #8a5a00;
  --color-warning-bg: #faefd6;
  --color-error: #a3312a;
  --color-error-bg: #f7e4e2;
  --color-info: #2d5b8a;
  --color-info-bg: #e3ecf5;
  --shadow-popover: 0 4px 16px rgba(28, 28, 25, 0.1);
  --shadow-dialog: 0 12px 40px rgba(28, 28, 25, 0.16);
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --sidebar-width: 232px;
  --font-sans: "IBM Plex Sans", system-ui, sans-serif;
  --font-serif: "Newsreader", Georgia, serif;
  --font-mono: "IBM Plex Mono", ui-monospace, monospace;
}

[data-theme="dark"] {
  --color-canvas: #131412;
  --color-surface: #1b1c1a;
  --color-sunken: #232421;
  --color-border-subtle: #30312d;
  --color-border-strong: #3d3e39;
  --color-text-primary: #eceae4;
  --color-text-secondary: #a9a69d;
  --color-text-tertiary: #8a877f;
  --color-action: #eceae4;
  --color-action-hover: #d8d6d0;
  --color-action-text: #131412;
  --color-brand: #d49ac4;
  --color-brand-hover: #e0b0d4;
  --color-brand-tint: #2a2228;
  --color-ochre: #d9a060;
  --color-ochre-tint: #2a2418;
  --color-success: #7dbb86;
  --color-success-bg: #1e2a20;
  --color-warning: #e0b354;
  --color-warning-bg: #2a2418;
  --color-error: #e8857c;
  --color-error-bg: #2a1e1c;
  --color-info: #7aa8d4;
  --color-info-bg: #1a2430;
}
""")

w("frontend/src/index.css", """@import "tailwindcss";
@import "./styles/tokens.css";

@theme {
  --font-sans: var(--font-sans);
  --font-serif: var(--font-serif);
  --font-mono: var(--font-mono);
}

@layer base {
  html {
    font-family: var(--font-sans);
    font-size: 14px;
    line-height: 22px;
    color: var(--color-text-primary);
    background: var(--color-canvas);
  }
  *:focus-visible {
    outline: 2px solid var(--color-brand);
    outline-offset: 2px;
  }
}

@layer utilities {
  .text-display { font-family: var(--font-serif); font-weight: 500; font-size: 32px; line-height: 40px; }
  .text-title { font-family: var(--font-serif); font-weight: 500; font-size: 24px; line-height: 32px; }
  .text-heading { font-size: 18px; line-height: 26px; font-weight: 600; }
  .text-subheading { font-size: 15px; line-height: 22px; font-weight: 600; }
  .text-label { font-size: 13px; line-height: 18px; font-weight: 500; }
  .text-caption { font-size: 12px; line-height: 16px; }
  .font-tabular { font-variant-numeric: tabular-nums; }
}
""")

w("frontend/src/lib/cn.ts", """import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}
""")

print("frontend styles ok")
