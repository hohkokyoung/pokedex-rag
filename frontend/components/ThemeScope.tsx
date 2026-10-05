"use client";

import { useEffect } from "react";

/**
 * Sets a boolean attribute on <html> for the lifetime of the page, so a scoped
 * theme in globals.css (e.g. `html[data-lab]`) can restyle the shared chrome
 * (nav, ambient) that lives above the route in the layout. Mirrors the home
 * page's `data-home` mechanism.
 */
export default function ThemeScope({ attr }: { attr: string }) {
  useEffect(() => {
    const el = document.documentElement;
    el.setAttribute(attr, "");
    return () => el.removeAttribute(attr);
  }, [attr]);
  return null;
}
