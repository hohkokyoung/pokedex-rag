/* How Milcery's spin evolution decides Alcremie's look (Pokémon Sword & Shield).
   PokéAPI only records the trigger ("spin") and the 63 form names, so these rules
   are hand-written game knowledge, keyed by the form-name parts the API returns. */

export const SPIN_STEPS = [
  "Give Milcery a Sweet to hold.",
  "In the overworld, rotate the control stick so your character spins in place.",
  "Stop spinning. Milcery evolves on the spot.",
];

/** Sweet held -> the decoration it puts on Alcremie. */
export const SWEET_TOPPING: Record<string, string> = {
  "Strawberry Sweet": "Strawberry",
  "Berry Sweet": "Berry",
  "Love Sweet": "Heart",
  "Star Sweet": "Star",
  "Clover Sweet": "Clover",
  "Flower Sweet": "Flower",
  "Ribbon Sweet": "Ribbon",
};

export type CreamRule = { direction: "Clockwise" | "Counter-clockwise"; duration: string; time: string };

/** Cream -> how to spin for it. Day/night follows the in-game clock. */
export const CREAM_RULE: Record<string, CreamRule> = {
  "Vanilla Cream": { direction: "Clockwise", duration: "Under 5 s", time: "Day" },
  "Ruby Cream": { direction: "Counter-clockwise", duration: "Under 5 s", time: "Day" },
  "Caramel Swirl": { direction: "Clockwise", duration: "Over 5 s", time: "Day" },
  "Ruby Swirl": { direction: "Counter-clockwise", duration: "Over 5 s", time: "Day" },
  "Lemon Cream": { direction: "Clockwise", duration: "Under 5 s", time: "Night" },
  "Matcha Cream": { direction: "Counter-clockwise", duration: "Under 5 s", time: "Night" },
  "Mint Cream": { direction: "Clockwise", duration: "Over 5 s", time: "Night" },
  "Salted Cream": { direction: "Counter-clockwise", duration: "Over 5 s", time: "Night" },
  "Rainbow Swirl": { direction: "Counter-clockwise", duration: "Over 10 s", time: "7:00–7:59 PM" },
};
