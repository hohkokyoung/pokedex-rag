import { Fragment, type ReactNode } from "react";

/** Renders a citation marker; the default is a plain "[n]" span. */
export type CiteRenderer = (n: number, key: string) => ReactNode;

const plainCite: CiteRenderer = (n, key) => <span key={key} className="lc-cite">[{n}]</span>;

/** Inline formatting: **bold** → <b>, [n]/【n】 → citation. */
export function renderInline(text: string, cite: CiteRenderer = plainCite, kp = ""): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|[[【]\d+[\]】])/g).map((p, k) => {
    const key = kp + k;
    if (/^\*\*[^*]+\*\*$/.test(p)) return <b key={key}>{p.slice(2, -2)}</b>;
    const m = p.match(/^[[【](\d+)[\]】]$/);
    if (m) return cite(Number(m[1]), key);
    return p ? <Fragment key={key}>{p}</Fragment> : null;
  });
}

export type AnswerBlock = { kind: "p"; text: string } | { kind: "ul"; items: string[] };

/**
 * Split a grounded answer into light-Markdown blocks: paragraphs and bullet /
 * numbered lists. A trailing, still-streaming line is included as-is.
 */
export function parseBlocks(text: string): AnswerBlock[] {
  const blocks: AnswerBlock[] = [];
  let list: string[] = [];
  let para: string[] = [];
  const flushPara = () => {
    if (para.length) blocks.push({ kind: "p", text: para.join(" ") });
    para = [];
  };
  const flushList = () => {
    if (list.length) blocks.push({ kind: "ul", items: list });
    list = [];
  };
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^[-*•]\s+(.*)/) ?? line.match(/^\d+\.\s+(.*)/);
    if (bullet) { flushPara(); list.push(bullet[1]); }
    else if (line === "") { flushList(); flushPara(); }
    else { flushList(); para.push(line); }
  }
  flushList();
  flushPara();
  return blocks;
}

/**
 * Render a grounded answer as light Markdown — paragraphs, bullet / numbered
 * lists, bold, and inline [n] citations — so structured answers read cleanly
 * instead of as one run-on paragraph. Used by the home Ask tiles; the /ask
 * console builds its own layout from `parseBlocks`.
 */
export function renderAnswer(text: string, cite?: CiteRenderer): ReactNode {
  return (
    <>
      {parseBlocks(text).map((b, i) =>
        b.kind === "p" ? (
          <p className="ans-p" key={i}>{renderInline(b.text, cite, `p${i}-`)}</p>
        ) : (
          <ul className="ans-ul" key={i}>
            {b.items.map((li, j) => <li key={j}>{renderInline(li, cite, `u${i}-${j}-`)}</li>)}
          </ul>
        ),
      )}
    </>
  );
}
