import type { Metadata } from "next";
import { Chakra_Petch, Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import SmoothScroll from "@/components/SmoothScroll";
import Nav from "@/components/Nav";
import ScrollProgress from "@/components/ScrollProgress";

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
      className={`${display.variable} ${sans.variable} ${mono.variable}`}
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
          <ScrollProgress />
          <Nav />
          {children}
        </SmoothScroll>
      </body>
    </html>
  );
}
