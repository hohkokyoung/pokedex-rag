import { Suspense } from "react";
import PokemonDetailView from "@/components/PokemonDetailView";
import ThemeScope from "@/components/ThemeScope";

export default async function PokemonPage({
  params,
}: {
  params: Promise<{ dex: string }>;
}) {
  const { dex } = await params;
  return (
    <>
      <ThemeScope attr="data-lab" />
      <Suspense fallback={null}>
        <PokemonDetailView key={dex} dex={dex} />
      </Suspense>
    </>
  );
}
