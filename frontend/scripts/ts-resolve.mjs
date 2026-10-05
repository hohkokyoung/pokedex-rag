// Lets Node run the frontend's TypeScript modules directly (Node strips types natively):
// extensionless relative imports ("./typeChart") resolve to the ".ts" file. Used by the
// damage reference-case generator; no build step or extra dependency.
import { registerHooks } from "node:module";

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier.startsWith(".") && !/\.[cm]?[jt]sx?$/.test(specifier)) {
      try {
        return nextResolve(`${specifier}.ts`, context);
      } catch {
        // fall through to Node's own resolution
      }
    }
    return nextResolve(specifier, context);
  },
});
