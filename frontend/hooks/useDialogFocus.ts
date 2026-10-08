"use client";

import { useEffect, useRef } from "react";

// The element to return to on close. Captured continuously (outside any modal),
// because an autoFocus field inside the dialog takes focus before effects run.
let lastOutside: HTMLElement | null = null;
if (typeof document !== "undefined") {
  document.addEventListener("focusin", (e) => {
    const el = e.target as HTMLElement | null;
    if (el && !el.closest('[aria-modal="true"]')) lastOutside = el;
  });
}

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Focus management for a modal dialog while `active`: moves focus inside (unless
 * an autoFocus field already took it), keeps Tab / Shift+Tab cycling within the
 * dialog, and returns focus to whatever opened it when it closes. Escape and
 * backdrop clicks stay with each dialog. Attach the returned ref to the element
 * with role="dialog".
 */
export function useDialogFocus<T extends HTMLElement = HTMLDivElement>(active: boolean) {
  const ref = useRef<T | null>(null);

  useEffect(() => {
    if (!active) return;
    const active0 = document.activeElement as HTMLElement | null;
    const opener = active0 && !active0.closest('[aria-modal="true"]') ? active0 : lastOutside;
    const node = ref.current;
    const focusables = () =>
      node
        ? [...node.querySelectorAll<HTMLElement>(FOCUSABLE)].filter((el) => el.getClientRects().length > 0)
        : [];

    if (node && !node.contains(document.activeElement)) {
      const first = focusables()[0];
      if (first) first.focus();
      else {
        node.tabIndex = -1;
        node.focus();
      }
    }

    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Tab" || !node) return;
      const items = focusables();
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      const inside = node.contains(document.activeElement);
      if (e.shiftKey && (document.activeElement === first || !inside)) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && (document.activeElement === last || !inside)) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      if (opener && opener.isConnected) opener.focus({ preventScroll: true });
    };
  }, [active]);

  return ref;
}
