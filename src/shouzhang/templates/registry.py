import json
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel, Field

from ..models.document import Canvas, Document, Layer
from ..models.element import ElementUnion, ImageElement, StickerElement, TextElement
from ..models.style import Style


class TemplateSlot(BaseModel):
    id: str
    type: str  # text / image / sticker
    x: float = 0.0
    y: float = 0.0
    w: float = 100.0
    h: float = 100.0
    rotation: float = 0.0
    default: str = ""
    style: Style = Field(default_factory=Style)


class Template(BaseModel):
    id: str
    name: str = ""
    category: str = "general"
    canvas: Canvas = Field(default_factory=Canvas)
    slots: list[TemplateSlot] = Field(default_factory=list)
    decorations: list[ElementUnion] = Field(default_factory=list)


class TemplateRegistry:
    """模板注册与加载。支持目录扫描 JSON，方便频繁扩充。"""

    def __init__(self) -> None:
        self._templates: dict[str, Template] = {}

    def register(self, template: Template) -> None:
        self._templates[template.id] = template

    def load_dir(self, path: Union[str, Path]) -> int:
        p = Path(path)
        if not p.is_dir():
            return 0
        count = 0
        for f in sorted(p.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            self.register(Template.model_validate(data))
            count += 1
        return count

    def get(self, template_id: str) -> Template:
        if template_id not in self._templates:
            raise KeyError(f"Template not found: {template_id}")
        return self._templates[template_id]

    def list(self, category: Optional[str] = None) -> list[Template]:
        if category:
            return [t for t in self._templates.values() if t.category == category]
        return list(self._templates.values())

    def categories(self) -> list[str]:
        return sorted({t.category for t in self._templates.values()})

    def instantiate(
        self,
        template_id: str,
        content: Optional[dict[str, str]] = None,
    ) -> Document:
        tpl = self.get(template_id)
        content = content or {}
        layer = Layer(id="main", name="主图层")
        z = 0
        for dec in tpl.decorations:
            dec.z_index = z
            z += 1
            layer.elements.append(dec.model_copy())
        for slot in tpl.slots:
            value = content.get(slot.id, slot.default)
            el = self._slot_to_element(slot, value, z)
            if el is not None:
                layer.elements.append(el)
                z += 1
        return Document(
            id="inst", name=tpl.name or tpl.id, canvas=tpl.canvas.model_copy(), layers=[layer]
        )

    def _slot_to_element(self, slot: TemplateSlot, value: str, z: int):
        common = dict(
            id=slot.id,
            x=slot.x, y=slot.y, w=slot.w, h=slot.h,
            rotation=slot.rotation, z_index=z, style=slot.style.model_copy(),
        )
        if slot.type == "text":
            return TextElement(**common, text=value)
        if slot.type == "image":
            return ImageElement(**common, src=value)
        if slot.type == "sticker":
            return StickerElement(**common, src=value)
        return None
