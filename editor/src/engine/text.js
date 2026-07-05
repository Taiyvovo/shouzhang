/**
 * 排版引擎 — 前端 JS 版
 * 与 Python engine/text_layout.py + engine/rich_text.py 逻辑完全一致
 */

// ── 字符宽度估算 ──
export function charWidth(ch, size) {
  const o = ch.codePointAt(0) || 0;
  if (o > 0x2e80) return size;        // CJK
  if (" \t".includes(ch)) return size * 0.28;
  if (".,;:!?\"'()[]{}".includes(ch)) return size * 0.3;
  if (/\d/.test(ch)) return size * 0.6;
  if (/[A-Z]/.test(ch)) return size * 0.68;
  if (/[a-z]/.test(ch)) return size * 0.55;
  return size * 0.5;
}

function wordWidth(word, size, ls) {
  let w = 0;
  for (const c of word) w += charWidth(c, size);
  return w + ls * word.length;
}

// ── 自动换行 ──
const TOKEN_RE = /[A-Za-z0-9]+(?:['\-][A-Za-z0-9]+)*|\s+|./g;

export function wrapText(text, size, boxWidth, letterSpacing = 0) {
  const out = [];
  for (const para of text.split("\n")) {
    if (!para) { out.push(""); continue; }
    let line = "", lineW = 0;
    const tokens = para.match(TOKEN_RE) || [];
    for (const tok of tokens) {
      if (/^\s+$/.test(tok)) {
        const tw = charWidth(tok[0], size) * tok.length + letterSpacing * tok.length;
        if (lineW + tw > boxWidth && line) {
          out.push(line.trimEnd()); line = ""; lineW = 0;
        } else {
          line += tok; lineW += tw;
        }
        continue;
      }
      const tw = wordWidth(tok, size, letterSpacing);
      if (tw > boxWidth && !line) {
        let hard = "", hardW = 0;
        for (const ch of tok) {
          const cw = charWidth(ch, size) + letterSpacing;
          if (hardW + cw > boxWidth && hard) {
            out.push(hard); hard = ch; hardW = cw;
          } else {
            hard += ch; hardW += cw;
          }
        }
        line = hard; lineW = hardW;
        continue;
      }
      if (lineW + tw > boxWidth && line) {
        out.push(line.trimEnd()); line = tok; lineW = tw;
      } else {
        line += tok; lineW += tw;
      }
    }
    out.push(line.trimEnd());
  }
  return out.join("\n");
}

// ── 富文本检测 ──
export function hasMarkup(text) {
  return /(\*\*|\*(?!\*)|__|~~|\[c=|\[s=)/.test(text);
}

// ── 富文本解析 ──
export function parseRichText(text) {
  const spans = [];
  let buf = "";

  function flush(extra = {}) {
    if (buf) { spans.push({ text: buf, bold: false, italic: false, underline: false, dots: false, color: null, size: null, ...extra }); buf = ""; }
  }

  function findClose(str, i, close) {
    let j = i;
    while (true) {
      j = str.indexOf(close, j);
      if (j === -1) return -1;
      if (j === 0 || str[j - 1] !== "\\") return j;
      j += close.length;
    }
  }

  let i = 0;
  const n = text.length;

  while (i < n) {
    if (text[i] === "\\" && i + 1 < n) { buf += text[i + 1]; i += 2; continue; }

    // **bold**  __underline__  ~~dots~~
    let matched = false;
    for (const [pat, close, attr] of [[/^\*\*(?!\*)/, "**", "bold"], [/^__(?!_)/, "__", "underline"], [/^~~(?!~)/, "~~", "dots"]]) {
      const m = text.slice(i).match(pat);
      if (m) {
        const tag = m[0];
        const end = findClose(text, i + tag.length, close);
        if (end !== -1) {
          flush();
          const inner = text.slice(i + tag.length, end);
          const sub = parseRichText(inner);
          for (const s of sub) s[attr] = true;
          spans.push(...sub);
          i = end + close.length;
          matched = true;
          break;
        }
      }
    }
    if (matched) continue;

    // *italic*
    if (text[i] === "*" && !text.startsWith("**", i)) {
      const end = findClose(text, i + 1, "*");
      if (end !== -1 && (end === n - 1 || text[end + 1] !== "*")) {
        flush();
        const inner = text.slice(i + 1, end);
        const sub = parseRichText(inner);
        for (const s of sub) s.italic = true;
        spans.push(...sub);
        i = end + 1;
        continue;
      }
    }

    // [c=#xxx]text[/c]
    const cm = text.slice(i).match(/^\[c=([^\]]+)\]/);
    if (cm) {
      const color = cm[1];
      const start = i + cm[0].length;
      const end = text.indexOf("[/c]", start);
      if (end !== -1) {
        flush();
        const inner = text.slice(start, end);
        const sub = parseRichText(inner);
        for (const s of sub) s.color = color;
        spans.push(...sub);
        i = end + 4;
        continue;
      }
    }

    // [s=N]text[/s]
    const sm = text.slice(i).match(/^\[s=([^\]]+)\]/);
    if (sm) {
      const sz = Number(sm[1]);
      if (!isNaN(sz)) {
        const start = i + sm[0].length;
        const end = text.indexOf("[/s]", start);
        if (end !== -1) {
          flush();
          const inner = text.slice(start, end);
          const sub = parseRichText(inner);
          for (const s of sub) s.size = sz;
          spans.push(...sub);
          i = end + 4;
          continue;
        }
      }
    }

    buf += text[i];
    i++;
  }

  flush();
  return spans;
}

// ── Span 宽度 ──
function spanWidth(sp, baseSize, ls) {
  const s = sp.size || baseSize;
  let w = 0;
  for (const c of sp.text) w += charWidth(c, s);
  return w + ls * sp.text.length;
}

// ── Span 换行 ──
function splitLong(text, size, boxW, ls) {
  const lines = [];
  let line = "", w = 0;
  for (const ch of text) {
    const cw = charWidth(ch, size) + ls;
    if (w + cw > boxW && line) { lines.push(line); line = ch; w = cw; }
    else { line += ch; w += cw; }
  }
  if (line) lines.push(line);
  return lines;
}

export function wrapSpans(spans, size, boxWidth, letterSpacing = 0) {
  const atoms = [];
  for (const sp of spans) {
    const parts = sp.text.split("\n");
    for (let pi = 0; pi < parts.length; pi++) {
      if (pi > 0) atoms.push(null);
      if (parts[pi]) atoms.push({ ...sp, text: parts[pi] });
    }
  }

  const out = [];
  let line = [], lineW = 0;

  for (const atom of atoms) {
    if (atom === null) { out.push(line); line = []; lineW = 0; continue; }

    const aw = spanWidth(atom, size, letterSpacing);
    if (lineW + aw > boxWidth && line.length) { out.push(line); line = []; lineW = 0; }

    if (aw > boxWidth && !line.length) {
      const subs = splitLong(atom.text, atom.size || size, boxWidth, letterSpacing);
      for (const st of subs) {
        out.push([{ ...atom, text: st }]);
      }
      continue;
    }

    line.push(atom); lineW += aw;
  }

  if (line.length) out.push(line);
  return out;
}

// ── 富文本还原纯文本 ──
export function richPlainText(spans) {
  return spans.map(s => s.text).join("");
}
