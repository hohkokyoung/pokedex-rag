"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import BrandMark from "./BrandMark";

// Icon paths shown in place of labels on phones (see .snav-icon in globals.css).
const ICONS: Record<string, React.ReactNode> = {
  "/": <path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" />,
  "/pokedex": (
    <>
      <rect x="4" y="3" width="16" height="18" rx="3" />
      <circle cx="12" cy="11" r="4" />
    </>
  ),
  "/teams": (
    <>
      <circle cx="7" cy="8" r="3" />
      <circle cx="17" cy="8" r="3" />
      <path d="M2 20c0-3 2.5-5 5-5s5 2 5 5M12 20c0-3 2.5-5 5-5s5 2 5 5" />
    </>
  ),
};

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/pokedex", label: "Pokédex" },
  { href: "/teams", label: "Teams" },
  { href: "/ask", label: "Ask", cta: true },
];

export default function Nav() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className="site-nav"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        transition: "background 0.3s, border-color 0.3s, backdrop-filter 0.3s",
        background: scrolled ? "color-mix(in oklab, var(--bg) 80%, transparent)" : "transparent",
        backdropFilter: scrolled ? "blur(14px) saturate(1.2)" : "none",
        borderBottom: scrolled ? "1px solid var(--line-soft)" : "1px solid transparent",
      }}
    >
      <nav className="shell snav">
        <Link href="/" className="snav-brand" aria-label="Pokédex home">
          <BrandMark className="snav-mark" />
          <span className="snav-word">pokérag</span>
        </Link>
        <div className="snav-links">
          <div className="snav-tray">
            {LINKS.filter((l) => !l.cta).map((l) => {
              const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  className={`snav-link${active ? " active" : ""}`}
                  aria-current={active ? "page" : undefined}
                  aria-label={l.label}
                >
                  <svg
                    className="snav-icon"
                    viewBox="0 0 24 24"
                    width="18"
                    height="18"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden
                  >
                    {ICONS[l.href]}
                  </svg>
                  <span className="snav-label">{l.label}</span>
                </Link>
              );
            })}
          </div>
          {LINKS.filter((l) => l.cta).map((l) => (
            <Link key={l.href} href={l.href} className="snav-link cta">
              {l.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
