declare module "vanta/dist/vanta.fog.min" {
  const effect: (opts: Record<string, unknown>) => { destroy: () => void };
  export default effect;
}

// three ships its own types but they don't resolve cleanly under bundler
// module resolution here; we only pass THREE through to Vanta, so `any` is fine.
declare module "three";
