import type { Metadata } from "next";
import { Suspense } from "react";
import AskConsole from "@/components/AskConsole";
import ThemeScope from "@/components/ThemeScope";

export const metadata: Metadata = {
  title: "pokerag — Ask",
  description: "Ask natural-language questions grounded in real Pokémon data, with citations.",
};

export default function AskPage() {
  return (
    <main className="shell ax-page">
      <ThemeScope attr="data-lab" />
      <header className="ax-hero">
        <div>
          <h1 className="font-display ax-hero__title">Ask the Pokédex</h1>
        </div>
        <p className="ax-hero__sub">
          Every answer cites the records it came from. If the data can’t answer, it says so
          instead of guessing.
        </p>
      </header>
      <Suspense>
        <AskConsole />
      </Suspense>
    </main>
  );
}
