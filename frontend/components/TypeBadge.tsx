import { titleCase, typeChip } from "@/lib/pokeTypes";

export default function TypeBadge({
  type,
  size = "md",
}: {
  type: string;
  size?: "sm" | "md";
}) {
  // Same face, size and weight as home's .lc-tt type tags (sans, bold, 12px).
  const pad = size === "sm" ? "3px 8px" : "4px 10px";
  const fs = 12;
  // Solid type pill — one design language with the home / moveset type tags.
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: pad,
        borderRadius: 6,
        fontSize: fs,
        fontWeight: 700,
        letterSpacing: "0.01em",
        textTransform: "capitalize",
        ...typeChip(type),
      }}
    >
      {titleCase(type)}
    </span>
  );
}
