from typing import Literal

from pydantic import BaseModel, Field

from .element import Element, ElementUnion


class Canvas(BaseModel):
    width: float = 1080.0
    height: float = 1527.0
    background: str = "#fdfaf3"
    pattern: Literal["none", "lines", "grid", "dots"] = "none"
    pattern_color: str = "rgba(0,0,0,0.06)"
    pattern_spacing: float = 28.0


class Layer(BaseModel):
    id: str
    name: str = "图层"
    visible: bool = True
    locked: bool = False
    elements: list[ElementUnion] = Field(default_factory=list)


class Document(BaseModel):
    id: str
    name: str = "未命名手账"
    canvas: Canvas = Field(default_factory=Canvas)
    layers: list[Layer] = Field(default_factory=list)

    def all_elements(self) -> list[Element]:
        elems = [
            e
            for layer in self.layers
            if layer.visible
            for e in layer.elements
            if e.visible
        ]
        return sorted(elems, key=lambda e: e.z_index)
