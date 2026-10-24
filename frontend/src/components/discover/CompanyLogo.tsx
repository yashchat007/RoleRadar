import { useState } from "react";
import { companyInitials } from "../../lib/companyBrand";

export function CompanyLogo({
  companyName,
  logoUrl,
  size = 32,
}: {
  companyName: string;
  logoUrl?: string | null;
  size?: number;
}) {
  const [failed, setFailed] = useState(false);
  const showImage = logoUrl && !failed;

  return (
    <span
      className="inline-flex shrink-0 items-center justify-center overflow-hidden rounded-[var(--radius-sm)] border border-[var(--color-border-subtle)] bg-[var(--color-sunken)]"
      style={{ width: size, height: size }}
    >
      {showImage ? (
        <img
          src={logoUrl}
          alt=""
          width={size}
          height={size}
          className="h-full w-full object-contain"
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="text-caption font-medium text-[var(--color-text-secondary)]" aria-hidden>
          {companyInitials(companyName)}
        </span>
      )}
    </span>
  );
}
