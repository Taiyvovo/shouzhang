"""字体注册表：扫描字体目录，按 family/weight/italic 查找。"""

import ctypes
import re
from pathlib import Path
from typing import Optional


_WEIGHT_MAP = {
    "thin": 100, "hairline": 100,
    "extralight": 200, "ultralight": 200,
    "light": 300,
    "regular": 400, "normal": 400, "": 400,
    "medium": 500,
    "semibold": 600, "demibold": 600,
    "bold": 700,
    "extrabold": 800, "ultrabold": 800,
    "black": 900, "heavy": 900,
}

_STYLE_RE = re.compile(
    r"[-_]?(thin|hairline|extralight|ultralight|light|regular|normal"
    r"|medium|semibold|demibold|bold|extrabold|ultrabold|black|heavy"
    r"|italic|oblique)",
    re.IGNORECASE,
)


class FontEntry:
    def __init__(self, path: Path, family: str, weight: int = 400, italic: bool = False) -> None:
        self.path = path
        self.family = family
        self.weight = weight
        self.italic = italic

    def __repr__(self) -> str:
        return f"FontEntry({self.family}, w={self.weight}, italic={self.italic})"


class FontRegistry:
    def __init__(self, font_dir: Optional[Path | str] = None) -> None:
        self.font_dir = Path(font_dir) if font_dir else None
        self._entries: list[FontEntry] = []
        self._by_family: dict[str, list[FontEntry]] = {}

    def scan(self, directory: Path | str | None = None) -> int:
        d = Path(directory) if directory else self.font_dir
        if not d or not d.is_dir():
            return 0
        count = 0
        for p in sorted(d.rglob("*")):
            if p.suffix.lower() not in (".ttf", ".otf"):
                continue
            entry = self._parse(p, d)
            self._entries.append(entry)
            key = entry.family.lower()
            if key not in self._by_family:
                self._by_family[key] = []
            self._by_family[key].append(entry)
            count += 1
        return count

    def _parse(self, path: Path, root: Path) -> FontEntry:
        stem = path.stem
        italic = False
        weight = 400

        parts = _STYLE_RE.split(stem)
        family_name = ""
        for part in parts:
            if part is None:
                continue
            part_stripped = part.strip("-")
            if part_stripped.lower() in _WEIGHT_MAP or part_stripped.lower() in ("italic", "oblique"):
                continue
            family_name += part_stripped
        if not family_name:
            family_name = stem

        family_name = " ".join(
            word[0].upper() + word[1:] if word.islower() and len(word) > 1 and word.isalpha()
            else word
            for word in re.findall(r"[A-Z]+[a-z]*|[a-z]+|[0-9]+", family_name)
        )
        if not family_name.strip():
            family_name = stem

        if re.search(r"[-_]?(italic|oblique)", stem, re.IGNORECASE):
            italic = True

        m = re.search(
            r"[-_](thin|hairline|extralight|ultralight|light|regular|normal"
            r"|medium|semibold|demibold|bold|extrabold|ultrabold|black|heavy)",
            stem,
            re.IGNORECASE,
        )
        if m:
            weight = _WEIGHT_MAP.get(m.group(1).lower(), 400)

        return FontEntry(path, family_name, weight, italic)

    def find(self, family: str, weight: int = 400, italic: bool = False) -> Optional[FontEntry]:
        entries = self._by_family.get(family.lower())
        if not entries:
            low = family.lower()
            for key, ents in self._by_family.items():
                if key == low or key.startswith(low + "-"):
                    entries = ents
                    break
        if not entries:
            return None
        best = None
        best_score = 99999
        for e in entries:
            wdiff = abs(e.weight - weight)
            idiff = 0 if e.italic == italic else (100 if italic else 50)
            score = wdiff + idiff
            if score < best_score:
                best_score = score
                best = e
        return best

    def list_families(self) -> list[str]:
        return sorted(self._by_family.keys())

    def get_entries(self, family: str) -> list[FontEntry]:
        return self._by_family.get(family.lower(), [])

    def install_to_process(self) -> int:
        """将已扫描字体装载到当前进程（Windows），resvg 可识别。"""
        count = 0
        for e in self._entries:
            try:
                ctypes.windll.gdi32.AddFontResourceExW(str(e.path), 0, 0)
                count += 1
            except OSError:
                pass
        return count
