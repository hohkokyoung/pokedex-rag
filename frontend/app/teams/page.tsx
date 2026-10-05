import type { Metadata } from "next";
import TeamsBrowser from "@/components/TeamsBrowser";
import ThemeScope from "@/components/ThemeScope";

export const metadata: Metadata = {
  title: "pokérag — Team Lab",
  description:
    "Build competitive teams, configure abilities, natures, EVs and moves, and get coached by the assistant.",
};

export default function TeamsPage() {
  return (
    <main className="shell" style={{ paddingTop: 92, paddingBottom: 100 }}>
      <ThemeScope attr="data-lab" />
      <header>
        <h1 className="font-display" style={{ fontSize: "clamp(2.2rem, 6vw, 4rem)" }}>
          Teams
        </h1>
        <p style={{ color: "var(--muted)", marginTop: 10, maxWidth: "58ch", lineHeight: 1.55 }}>
          Build a team and see how it rates. Open any team to test it against another one.
        </p>
      </header>
      <TeamsBrowser />
    </main>
  );
}
