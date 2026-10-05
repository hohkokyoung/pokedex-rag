"use client";

import { useRef } from "react";

/**
 * Wraps content so it eases toward the pointer on hover (magnetic effect),
 * springing back on leave. Disabled for touch/reduced-motion via CSS hover.
 */
export default function Magnetic({
  children,
  strength = 0.4,
  className,
}: {
  children: React.ReactNode;
  strength?: number;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement | null>(null);

  function onMove(e: React.MouseEvent) {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const x = e.clientX - (r.left + r.width / 2);
    const y = e.clientY - (r.top + r.height / 2);
    el.style.transform = `translate(${x * strength}px, ${y * strength}px)`;
  }
  function onLeave() {
    if (ref.current) ref.current.style.transform = "translate(0, 0)";
  }

  return (
    <span
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className={className}
      style={{
        display: "inline-flex",
        transition: "transform 0.5s var(--ease-out-expo)",
        willChange: "transform",
      }}
    >
      {children}
    </span>
  );
}
