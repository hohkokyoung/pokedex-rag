import type { Metadata } from "next";
import {
  Chakra_Petch,
  Space_Grotesk,
  JetBrains_Mono,
  Bodoni_Moda,
  Archivo,
  Inter,
} from "next/font/google";
import "./globals.css";
import SmoothScroll from "@/components/SmoothScroll";
import Nav from "@/components/Nav";
import ScrollProgress from "@/components/ScrollProgress";
import PointerFX from "@/components/PointerFX";

const display = Chakra_Petch({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const sans = Space_Grotesk({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const mono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

// High-contrast Didone serif + heavy grotesk — used by the redesigned home page.
const serif = Bodoni_Moda({
  variable: "--font-serif",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
});

const grotesk = Archivo({
  variable: "--font-grotesk",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
});

// Light-weight grotesque for the "generated-light" home redesign.
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["300", "400", "500"],
});

export const metadata: Metadata = {
  title: "pokérag",
  description:
    "A premium Pokédex device with an AI research assistant grounded in real Pokémon data.",
};

const THEME_SCOPE_SCRIPT = `document.documentElement.setAttribute(location.pathname==="/"?"data-home":"data-lab","")`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${sans.variable} ${mono.variable} ${serif.variable} ${grotesk.variable} ${inter.variable}`}
      suppressHydrationWarning
    >
      <head>
        {/* Set the route's light-theme scope (home's data-home / ThemeScope's
            data-lab) before first paint; otherwise a hard refresh flashes the
            default HUD theme until those effects run after hydration. */}
        <script dangerouslySetInnerHTML={{ __html: THEME_SCOPE_SCRIPT }} />
      </head>
      <body>
        <SmoothScroll>
          <PointerFX />
          <div className="hud-ambient" aria-hidden>
            <div className="hud-ambient__grid" />
            <div className="hud-ambient__scan" />
            <div className="hud-ambient__vignette" />
          </div>
          <ScrollProgress />
          <Nav />
          {children}
        </SmoothScroll>
      </body>
    </html>
  );
}
