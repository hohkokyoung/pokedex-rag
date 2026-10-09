// Lets Node run the frontend's TypeScript modules directly (Node strips types natively):
// extensionless relative and "@/…" imports ("./typeChart", "@/lib/api") resolve to the
// ".ts" file. Used by the reference-case generators; no build step or extra dependency.
import { registerHooks } from "node:module";

registerHooks({
  resolve(specifier, context, nextResolve) {
    // The "@/…" path alias (tsconfig) points at the frontend root.
    if (specifier.startsWith("@/")) specifier = new URL(`../${specifier.slice(2)}`, import.meta.url).href;
    if ((specifier.startsWith(".") || specifier.startsWith("file:"))&& !/\.[cm]?[jt]sx?$/.test(specifier)) {
      try {
        return nextResolve(`${specifier}.ts`, context);
      } catch {
        // fall through to Node's own resolution
      }
    }
    return nextResolve(specifier, context);
  },
});
