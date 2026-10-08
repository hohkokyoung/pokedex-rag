import { STAT_LABELS, typeText } from "@/lib/pokeTypes";
import type { PokemonDetail } from "@/lib/types";

function genderText(rate: number | null): { male: string; female: string } | "genderless" {
  if (rate === null || rate < 0) return "genderless";
  const female = (rate / 8) * 100;
  const fmt = (n: number) => (Number.isInteger(n) ? `${n}` : n.toFixed(1));
  return { male: `${fmt(100 - female)}%`, female: `${fmt(female)}%` };
}

function evText(ev: Record<string, number>): string {
  const parts = STAT_LABELS.filter((s) => ev[s.key]).map((s) => `${ev[s.key]} ${s.label}`);
  return parts.length ? parts.join(", ") : "None";
}

function Item({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="tb__k">{label}</div>
      <div className="tb__v">{children}</div>
    </div>
  );
}

/** Training & breeding info (T-001): gender, eggs, growth, EV yield. */
export default function TrainingBreeding({ d }: { d: PokemonDetail }) {
  const gender = genderText(d.gender_rate);
  const steps =
    d.hatch_counter != null ? ((d.hatch_counter + 1) * 255).toLocaleString() : null;

  return (
    <div className="tb">
      <Item label="Gender ratio">
        {gender === "genderless" ? (
          <span style={{ color: "var(--muted)" }}>Genderless</span>
        ) : (
          <span>
            <span style={{ color: typeText("water") }}>♂ {gender.male}</span>
            <span style={{ color: "var(--faint)", margin: "0 8px" }}>·</span>
            <span style={{ color: typeText("fairy") }}>♀ {gender.female}</span>
          </span>
        )}
      </Item>

      <Item label="Egg groups">
        {d.egg_groups.length ? (
          <div className="tb__chips">
            {d.egg_groups.map((g) => (
              <span key={g} className="tb__chip font-mono">{g}</span>
            ))}
          </div>
        ) : (
          <span style={{ color: "var(--muted)" }}>—</span>
        )}
      </Item>

      <Item label="Egg cycles">
        {d.hatch_counter != null ? (
          <>
            {d.hatch_counter} cycles{" "}
            <span style={{ color: "var(--faint)", fontSize: 12 }}>· ~{steps} steps</span>
          </>
        ) : (
          "—"
        )}
      </Item>

      <Item label="Growth rate">{d.growth_rate ?? "—"}</Item>
      <Item label="EV yield">{evText(d.ev_yield)}</Item>
      <Item label="Base friendship">{d.base_happiness ?? "—"}</Item>
    </div>
  );
}
