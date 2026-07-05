"""富文本标记解析：把带标记的文本拆成 styled spans。"""

import re
from typing import Optional

from ..models.style import TextSpan


_MARKUP = [
    # (open_regex, close_str, attr_name, value)
    (r"\*\*(?!\*)", "**", "bold", True),
    (r"__(?!_)", "__", "underline", True),
    (r"~~(?!~)", "~~", "dots", True),
]


def _find_close(text: str, i: int, close: str) -> int:
    """查找闭合标记位置，跳过被转义的。"""
    j = i
    while True:
        j = text.find(close, j)
        if j == -1:
            return -1
        if j == 0 or text[j - 1] != "\\":
            return j
        j += len(close)


def parse_rich_text(text: str) -> list[TextSpan]:
    """解析富文本标记，返回 TextSpan 列表。无标记的纯文本退化为单个 span。"""
    spans: list[TextSpan] = []
    buf: str = ""

    def flush(**kw) -> None:
        nonlocal buf
        if buf:
            spans.append(TextSpan(text=buf, **kw))
            buf = ""

    i = 0
    n = len(text)
    while i < n:
        if text[i] == "\\" and i + 1 < n:
            buf += text[i + 1]
            i += 2
            continue

        # 尝试匹配 markup 标记（** __ ~~）
        matched = False
        for pat, close, attr, val in _MARKUP:
            m = re.match(pat, text[i:])
            if m:
                tag = m.group(0)
                end = _find_close(text, i + len(tag), close)
                if end != -1:
                    flush()
                    inner = text[i + len(tag) : end]
                    kwargs: dict = {attr: val}
                    spans.extend(parse_rich_text(inner))
                    # 递归解析后的结果全部打上当前样式
                    for s in spans[-len(parse_rich_text(inner)):]:
                        setattr(s, attr, True)
                    i = end + len(close)
                    matched = True
                    break
        if matched:
            continue

        # 斜体 *...*（单星号，前后不能是星号）
        if text[i] == "*" and not text[i : i + 2] == "**":
            end = _find_close(text, i + 1, "*")
            if end != -1 and (end == n - 1 or text[end + 1] != "*"):
                flush()
                inner = text[i + 1 : end]
                sub = parse_rich_text(inner)
                for s in sub:
                    s.italic = True
                spans.extend(sub)
                i = end + 1
                continue

        # 颜色 [c=#xxx]text[/c]
        m = re.match(r"\[c=([^\]]+)\]", text[i:])
        if m:
            color = m.group(1)
            start = i + len(m.group(0))
            end = text.find("[/c]", start)
            if end != -1:
                flush()
                inner = text[start:end]
                sub = parse_rich_text(inner)
                for s in sub:
                    s.color = color
                spans.extend(sub)
                i = end + 4
                continue

        # 字号 [s=N]text[/s]
        m = re.match(r"\[s=([^\]]+)\]", text[i:])
        if m:
            try:
                size = float(m.group(1))
            except ValueError:
                buf += text[i]
                i += 1
                continue
            start = i + len(m.group(0))
            end = text.find("[/s]", start)
            if end != -1:
                flush()
                inner = text[start:end]
                sub = parse_rich_text(inner)
                for s in sub:
                    s.size_override = size
                spans.extend(sub)
                i = end + 4
                continue

        buf += text[i]
        i += 1

    flush()
    return spans


def rich_plain_text(spans: list[TextSpan]) -> str:
    return "".join(s.text for s in spans)


def has_markup(text: str) -> bool:
    return re.search(r"(\*\*|\*(?!\*)|__|~~|\[c=|\[s=)", text) is not None


from .text_layout import char_width


def _span_w(sp: TextSpan, base_size: float, ls: float) -> float:
    s = sp.size_override if sp.size_override else base_size
    return sum(char_width(c, s) for c in sp.text) + ls * len(sp.text)


def _split_long(text: str, size: float, box_w: float, ls: float) -> list[str]:
    """把一个超长纯文本切分到多行。"""
    lines: list[str] = []
    line = ""
    w = 0.0
    for ch in text:
        cw = char_width(ch, size) + ls
        if w + cw > box_w and line:
            lines.append(line)
            line = ch
            w = cw
        else:
            line += ch
            w += cw
    if line:
        lines.append(line)
    return lines


def wrap_spans(
    spans: list[TextSpan],
    size: float,
    box_width: float,
    letter_spacing: float = 0.0,
) -> list[list[TextSpan]]:
    """把 styled spans 按框宽带换行成多行，每行是子 span 列表。"""
    atoms: list[TextSpan | None] = []
    for sp in spans:
        parts = sp.text.split("\n")
        for pi, part in enumerate(parts):
            if pi > 0:
                atoms.append(None)
            if part:
                atoms.append(
                    TextSpan(
                        text=part,
                        bold=sp.bold,
                        italic=sp.italic,
                        underline=sp.underline,
                        dots=sp.dots,
                        color=sp.color,
                        size_override=sp.size_override,
                    )
                )

    lines_out: list[list[TextSpan]] = []
    line: list[TextSpan] = []
    line_w: float = 0.0

    for atom in atoms:
        if atom is None:
            lines_out.append(line)
            line = []
            line_w = 0.0
            continue

        aw = _span_w(atom, size, letter_spacing)
        if line_w + aw > box_width and line:
            lines_out.append(line)
            line = []
            line_w = 0.0

        if aw > box_width and not line:
            sub_texts = _split_long(atom.text, atom.size_override or size, box_width, letter_spacing)
            for st in sub_texts:
                sub_sp = TextSpan(
                    text=st,
                    bold=atom.bold,
                    italic=atom.italic,
                    underline=atom.underline,
                    dots=atom.dots,
                    color=atom.color,
                    size_override=atom.size_override,
                )
                lines_out.append([sub_sp])
            continue

        line.append(atom)
        line_w += aw

    if line:
        lines_out.append(line)

    return lines_out
