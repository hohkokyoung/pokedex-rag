import type { Metadata } from "next";
import TeamWorkbench from "@/components/TeamWorkbench";
import ThemeScope from "@/components/ThemeScope";

export const metadata: Metadata = {
  title: "pokérag — Team",
  description: "Configure a team's slots and get coached on what to improve.",
};

export default async function TeamPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ vs?: string; new?: string }>;
}) {
  const [{ id }, { vs, new: fresh }] = await Promise.all([params, searchParams]);
  const opponentId = Number(vs);
  return (
    <>
      <ThemeScope attr="data-lab" />
      <TeamWorkbench
        teamId={Number(id)}
        initialOpponentId={Number.isInteger(opponentId) && opponentId > 0 ? opponentId : null}
        isDraft={fresh === "1"}
      />
    </>
  );
}
