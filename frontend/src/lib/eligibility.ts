export type EligibilityLabel = "Eligible" | "Potential eligibility issue" | "Eligibility unclear";

export function eligibilityTone(
  label: string | null | undefined,
): "success" | "warning" | "error" | "neutral" {
  if (label === "Eligible") return "success";
  if (label === "Potential eligibility issue") return "warning";
  if (label === "Eligibility unclear") return "neutral";
  return "neutral";
}
