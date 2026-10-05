// "Dex Lens" brand mark — same geometry as public/brand/pokedex-os-symbol.svg.
export default function BrandMark({ size = 22, className }: { size?: number; className?: string }) {
  return (
    <svg
      viewBox="32 24 192 208"
      width={(size * 192) / 208}
      height={size}
      className={className}
      aria-hidden
    >
      <path
        fill="#e3350d"
        d="M32 48A24 24 0 0 1 56 24L161.37 24A16 16 0 0 1 172.69 28.69L219.31 75.31A16 16 0 0 1 224 86.63L224 208A24 24 0 0 1 200 232L56 232A24 24 0 0 1 32 208Z"
      />
      <circle cx="112" cy="128" r="64" fill="#fff" />
      <circle cx="112" cy="128" r="44" fill="#2f7bf5" />
      <circle cx="96.16" cy="112.16" r="12" fill="#fff" />
    </svg>
  );
}
