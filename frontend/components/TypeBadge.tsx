import { titleCase, typeColor } from "@/lib/pokeTypes";

export default function TypeBadge({
  type,
  size = "md",
}: {
  type: string;
  size?: "sm" | "md";
}) {
  const color = typeColor(type);
  const pad = size === "sm" ? "3px 9px" : "4px 11px";
  const fs = size === "sm" ? 10 : 11;
  // Solid type pill — one design language with the home / moveset type tags.
  return (
    <span
      className="font-mono"
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: pad,
        borderRadius: 6,
        fontSize: fs,
        fontWeight: 700,
        letterSpacing: "0.06em",
        textTransform: "capitalize",
        color: "#fff",
        background: color,
      }}
    >
      {titleCase(type)}
    </span>
  );
}
