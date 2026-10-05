// A template re-mounts on every navigation, so this animates page content
// in on each route change (subtle fade + rise + de-blur).
export default function Template({ children }: { children: React.ReactNode }) {
  return <div className="page-enter">{children}</div>;
}
