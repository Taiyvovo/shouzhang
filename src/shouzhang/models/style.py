from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Direction(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Align(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VAlign(str, Enum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class FontStyle(BaseModel):
    family: str = "sans-serif"
    size: float = 16.0
    weight: int = 400
    color: str = "#2b2b2b"
    line_height: float = 1.6
    letter_spacing: float = 0.0
    italic: bool = False
    underline: bool = False


class FillStyle(BaseModel):
    type: Literal["none", "solid", "linear", "pattern"] = "none"
    color: str = "#ffffff"
    gradient_colors: list[str] = Field(default_factory=list)
    gradient_angle: float = 0.0
    pattern_src: Optional[str] = None


class BorderStyle(BaseModel):
    color: str = "#000000"
    width: float = 0.0
    style: Literal["solid", "dashed", "dotted"] = "solid"
    radius: float = 0.0


class ShadowStyle(BaseModel):
    color: str = "rgba(0,0,0,0.18)"
    blur: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 2.0


class Style(BaseModel):
    font: FontStyle = Field(default_factory=FontStyle)
    fill: FillStyle = Field(default_factory=FillStyle)
    border: BorderStyle = Field(default_factory=BorderStyle)
    shadow: ShadowStyle = Field(default_factory=ShadowStyle)
    opacity: float = 1.0


class TextSpan(BaseModel):
    """一个带样式的文本片段，支持 inline 样式。"""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    dots: bool = False
    color: Optional[str] = None
    size_override: Optional[float] = None
