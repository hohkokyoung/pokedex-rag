import type { Metadata } from "next";
import PokedexBrowser from "@/components/PokedexBrowser";
import ThemeScope from "@/components/ThemeScope";

export const metadata: Metadata = {
  title: "pokérag — Catalog",
  description: "Browse, search and filter all 1025 Pokémon by type, generation and stats.",
};

export default function PokedexPage() {
  return (
    <main className="shell" style={{ paddingTop: 92, paddingBottom: 80 }}>
      <ThemeScope attr="data-lab" />
      <header style={{ marginBottom: 8 }}>
        <h1 className="font-display" style={{ fontSize: "clamp(2.2rem, 6vw, 4rem)" }}>
          Pokédex
        </h1>
      </header>
      <PokedexBrowser />
    </main>
  );
}
