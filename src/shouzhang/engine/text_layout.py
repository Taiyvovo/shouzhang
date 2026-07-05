"""文本自动换行：按文本框宽度切分，中英文混排。逐字符估算宽度，英文按词不断开。"""

import re


def char_width(ch: str, size: float) -> float:
    o = ord(ch)
    if o > 0x2E80:
        return size
    if ch in " \t":
        return size * 0.28
    if ch in ".,;:!?\"'()[]{}":
        return size * 0.3
    if ch.isdigit():
        return size * 0.6
    if ch.isupper():
        return size * 0.68
    if ch.isalpha():
        return size * 0.55
    return size * 0.5


def _word_width(word: str, size: float, ls: float) -> float:
    return sum(char_width(c, size) for c in word) + ls * len(word)


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['\-][A-Za-z0-9]+)*|\s+|.")


def wrap_text(text: str, size: float, box_width: float, letter_spacing: float = 0.0) -> str:
    out_lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            out_lines.append("")
            continue
        line = ""
        line_w = 0.0
        for token in _TOKEN_RE.findall(paragraph):
            if token.isspace():
                tw = char_width(token[0], size) * len(token) + letter_spacing * len(token)
                if line_w + tw > box_width and line:
                    out_lines.append(line.rstrip())
                    line = ""
                    line_w = 0.0
                else:
                    line += token
                    line_w += tw
                continue
            tw = _word_width(token, size, letter_spacing)
            if tw > box_width and not line:
                hard = ""
                hard_w = 0.0
                for ch in token:
                    cw = char_width(ch, size) + letter_spacing
                    if hard_w + cw > box_width and hard:
                        out_lines.append(hard)
                        hard = ch
                        hard_w = cw
                    else:
                        hard += ch
                        hard_w += cw
                line = hard
                line_w = hard_w
                continue
            if line_w + tw > box_width and line:
                out_lines.append(line.rstrip())
                line = token
                line_w = tw
            else:
                line += token
                line_w += tw
        out_lines.append(line.rstrip())
    return "\n".join(out_lines)
