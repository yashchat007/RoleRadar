export function careerPageDomain(careerPageUrl: string): string | null {
  try {
    const host = new URL(careerPageUrl).hostname.toLowerCase();
    return host.replace(/^www\./, "") || null;
  } catch {
    return null;
  }
}

export function companyLogoUrl(careerPageUrl: string): string | null {
  const domain = careerPageDomain(careerPageUrl);
  if (!domain) return null;
  return `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=128`;
}

export function companyInitials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}
