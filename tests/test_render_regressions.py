from pathlib import Path

import pytest

from shouzhang.models.document import Canvas, Document, Layer
from shouzhang.models.element import StickerElement, TextElement
from shouzhang.models.style import ShadowStyle, Style
from shouzhang.render import DocumentCompiler, SVGCompiler


def test_shadow_compiles_to_svg() -> None:
    element = TextElement(
        id="text",
        text="shadow",
        style=Style(shadow=ShadowStyle(blur=4, offset_x=1, offset_y=2)),
    )
    document = Document(id="doc", canvas=Canvas(), layers=[Layer(id="main", elements=[element])])

    svg = SVGCompiler().render(DocumentCompiler().compile(document))

    assert '<filter id="sh0"' in svg
    assert 'filter="url(#sh0)"' in svg


def test_hidden_elements_are_not_compiled() -> None:
    document = Document(
        id="doc",
        layers=[Layer(id="main", elements=[TextElement(id="secret", text="SECRET", visible=False)])],
    )

    svg = SVGCompiler().render(DocumentCompiler().compile(document))

    assert "SECRET" not in svg


def test_assets_cannot_escape_root(tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    outside = tmp_path / "outside.svg"
    outside.write_text('<svg viewBox="0 0 1 1"></svg>', encoding="utf-8")
    document = Document(
        id="doc",
        layers=[Layer(id="main", elements=[StickerElement(id="bad", src="../outside.svg")])],
    )

    with pytest.raises(ValueError, match="escapes"):
        DocumentCompiler(assets_root=assets, restrict_assets=True).compile(document)


def test_svg_attributes_are_escaped() -> None:
    element = TextElement(id="text", text="safe", style=Style())
    element.style.font.family = 'bad\" onload=\"alert(1)'
    document = Document(id="doc", layers=[Layer(id="main", elements=[element])])

    svg = SVGCompiler().render(DocumentCompiler().compile(document))

    assert 'onload="alert(1)"' not in svg
    assert "bad&quot; onload=&quot;alert(1)" in svg
