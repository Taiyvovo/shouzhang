import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union


DEFAULT_EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


class Rasterizer:
    """SVG → PNG。多后端。支持 Edge headless 渲染 @font-face 字体。"""

    def __init__(self) -> None:
        self._backends = self._detect_backends()
        self._edge_path: Optional[str] = self._find_edge()

    def _detect_backends(self) -> list[str]:
        backends: list[str] = []
        try:
            import resvg_py  # noqa: F401
            backends.append("resvg")
        except Exception:
            pass
        try:
            import cairosvg  # noqa: F401
            backends.append("cairosvg")
        except Exception:
            pass
        return backends

    def _find_edge(self) -> Optional[str]:
        import shutil
        for p in DEFAULT_EDGE_PATHS:
            if Path(p).exists():
                return p
        found = shutil.which("msedge") or shutil.which("chrome") or shutil.which("chromium")
        return str(found) if found else None

    def available(self) -> bool:
        return bool(self._backends)

    @property
    def backend(self) -> Optional[str]:
        return self._backends[0] if self._backends else None

    def has_browser(self) -> bool:
        return self._edge_path is not None

    def to_png(
        self,
        svg: str,
        output_width: Optional[int] = None,
        output_height: Optional[int] = None,
        scale: float = 1.0,
        resources_dir: Optional[Union[str, Path]] = None,
        use_browser: bool = False,
    ) -> bytes:
        if use_browser and self._edge_path:
            return self._with_edge(svg, output_width, output_height, scale)
        if not self._backends:
            raise RuntimeError(
                "No PNG backend. Install one: pip install resvg-py"
            )
        last_err: Optional[Exception] = None
        for b in self._backends:
            try:
                if b == "resvg":
                    return self._with_resvg(svg, output_width, output_height, scale, resources_dir)
                if b == "cairosvg":
                    return self._with_cairosvg(svg, output_width, output_height, scale)
            except Exception as e:
                last_err = e
        raise RuntimeError(f"All PNG backends failed: {last_err}")

    def _with_edge(
        self, svg: str, w: Optional[int], h: Optional[int], scale: float
    ) -> bytes:
        assert self._edge_path
        ow, oh = self._resolve_size(svg, w, h, scale)
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ margin:0; background:#fff; }}
svg {{ display:block; }}
</style></head><body>
{svg}
</body></html>"""

        with tempfile.NamedTemporaryFile(
            suffix="_w.html", mode="w", encoding="utf-8", delete=False
        ) as tf:
            tf.write(html)
            html_path = tf.name

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as pf:
            png_path = pf.name

        try:
            result = subprocess.run(
                [
                    self._edge_path,
                    "--headless=new",
                    "--disable-gpu",
                    f"--screenshot={png_path}",
                    f"--window-size={ow},{oh}",
                    f"--force-device-scale-factor={scale if scale > 0 else 1.0}",
                    html_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Edge exited with {result.returncode}: {result.stderr[:500]}"
                )
            return Path(png_path).read_bytes()
        finally:
            Path(html_path).unlink(missing_ok=True)
            Path(png_path).unlink(missing_ok=True)

    def _resolve_size(
        self, svg: str, w: Optional[int], h: Optional[int], scale: float
    ) -> tuple[int, int]:
        sw, sh = self._svg_size(svg)
        if w is None and h is None:
            if scale != 1.0:
                return int(sw * scale), int(sh * scale)
            return int(sw), int(sh)
        if w is None:
            w = int(h * sw / sh) if sh else int(sh)
        if h is None:
            h = int(w * sh / sw) if sw else int(sw)
        return int(w), int(h)

    def _with_resvg(
        self, svg: str, w: Optional[int], h: Optional[int], scale: float,
        resources_dir: Optional[Union[str, Path]] = None,
    ) -> bytes:
        import resvg_py

        ow, oh = self._resolve_size(svg, w, h, scale)
        kwargs: dict = {"svg_string": svg, "width": ow, "height": oh}
        if resources_dir:
            kwargs["resources_dir"] = str(resources_dir)
        return resvg_py.svg_to_bytes(**kwargs)

    def _with_cairosvg(
        self, svg: str, w: Optional[int], h: Optional[int], scale: float
    ) -> bytes:
        import cairosvg

        ow, oh = self._resolve_size(svg, w, h, scale)
        kwargs: dict = {"bytestring": svg.encode("utf-8")}
        if ow:
            kwargs["output_width"] = ow
        if oh:
            kwargs["output_height"] = oh
        return cairosvg.svg2png(**kwargs)

    def to_file(
        self,
        svg: str,
        path: Union[str, Path],
        output_width: Optional[int] = None,
        output_height: Optional[int] = None,
        scale: float = 1.0,
        resources_dir: Optional[Union[str, Path]] = None,
        use_browser: bool = False,
    ) -> Path:
        data = self.to_png(svg, output_width, output_height, scale, resources_dir, use_browser)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p

    def _svg_size(self, svg: str) -> tuple[float, float]:
        mw = re.search(r'<svg[^>]*\swidth="([\d.]+)"', svg)
        mh = re.search(r'<svg[^>]*\sheight="([\d.]+)"', svg)
        if not mw or not mh:
            mvb = re.search(r'viewBox="([\d.\s\-]+)"', svg)
            if mvb:
                parts = mvb.group(1).split()
                return float(parts[2]), float(parts[3])
        w = float(mw.group(1)) if mw else 1080.0
        h = float(mh.group(1)) if mh else 1350.0
        return w, h
