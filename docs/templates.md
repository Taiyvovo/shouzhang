# 模板 JSON 参考

模板文件放在 `src/shouzhang/templates/builtin/*.json`，加载后自动可用。

## 完整结构

```json
{
  "id": "my-template",
  "name": "我的模板",
  "category": "diary",
  "canvas": { ... },
  "slots": [ ... ],
  "decorations": [ ... ]
}
```

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | ✅ | 唯一 ID，用作文件名和引用 |
| `name` | string | ❌ | 显示名称，默认用 id |
| `category` | string | ❌ | `"diary"` 或 `"hand"`，用于分组 |
| `canvas` | object | ❌ | 画布设置 |
| `slots` | array | ❌ | 可编辑的内容槽位 |
| `decorations` | array | ❌ | 固定装饰元素 |

---

## Canvas（画布）

```json
{
  "width": 1080,
  "height": 1527,
  "background": "#fbfaf6",
  "pattern": "lines",
  "pattern_color": "rgba(160,150,130,0.20)",
  "pattern_spacing": 36
}
```

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `width` | float | 1080 | 画布宽度 (px)。竖版 1080，横版 1527 |
| `height` | float | 1527 | 画布高度 (px)。竖版 1527，横版 1080 |
| `background` | color | `"#fdfaf3"` | 背景颜色 |
| `pattern` | enum | `"none"` | `"none"` / `"lines"` / `"grid"` / `"dots"` |
| `pattern_color` | color | — | 图案颜色，支持 rgba |
| `pattern_spacing` | float | 28 | 线/点间距 (px) |

### 常用画布尺寸

| 用途 | width | height |
|---|---|---|
| A5 竖版（日记默认） | 1080 | 1527 |
| A5 横版 | 1527 | 1080 |

---

## Slots（内容槽位）

用于定义可替换的文字、图片、贴纸区域。`instantiate()` 时可通过 `content` 字典替换 `default` 值。

```json
{
  "id": "title",
  "type": "text",
  "x": 80, "y": 120,
  "w": 920, "h": 80,
  "default": "标题文字",
  "style": {
    "font": {
      "family": "serif",
      "size": 48,
      "weight": 700,
      "color": "#3a3026",
      "line_height": 1.5,
      "letter_spacing": 0
    }
  }
}
```

### 通用字段

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `id` | string | — | 槽位 ID，用于 content 覆盖 |
| `type` | enum | — | `"text"` / `"image"` / `"sticker"` |
| `x` | float | 0 | 左上角 X 坐标 |
| `y` | float | 0 | 左上角 Y 坐标 |
| `w` | float | 100 | 槽位宽度 |
| `h` | float | 100 | 槽位高度 |
| `rotation` | float | 0 | 旋转角度（度） |
| `default` | string | `""` | 默认内容（text 时是文本，image/sticker 时是路径） |
| `style` | object | — | 样式设置 |

### Style 结构

```json
{
  "font": {
    "family": "Noto Sans SC",
    "size": 36,
    "weight": 400,
    "color": "#333",
    "line_height": 2.0,
    "letter_spacing": 0
  },
  "opacity": 1.0
}
```

#### Font 字段

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `family` | string | `"sans-serif"` | CSS font-family 名。参考 [fonts.md](fonts.md) |
| `size` | float | 16 | 字号 (px) |
| `weight` | int | 400 | 字重。400=正常，700=粗体，100=细体 |
| `color` | color | `"#2b2b2b"` | 文字颜色 |
| `line_height` | float | 1.6 | 行高倍数 |
| `letter_spacing` | float | 0 | 字间距 (px) |

---

## Decorations（装饰元素）

固定装饰，不受 content 替换影响。每个元素直接是一个 Element 对象。

### 贴纸 Sticker

```json
{
  "type": "sticker",
  "id": "moon",
  "x": 100, "y": 200,
  "w": 80, "h": 80,
  "rotation": 15,
  "src": "stickers/moon.svg"
}
```

src 路径相对于 `assets/` 目录。可用贴纸见 [assets.md](assets.md)。

### 背景图 Background

```json
{
  "type": "background",
  "svg": "kraft"
}
```

`svg` 可选 `"kraft"`（牛皮纸纹理）或 `"mint"`（薄荷网格）。背景图自动铺满画布。

### 胶带 Tape

```json
{
  "type": "tape",
  "id": "tape1",
  "x": 400, "y": 100,
  "w": 180, "h": 44,
  "rotation": -5,
  "src": "tapes/washi-1.svg"
}
```

---

## 完整示例（经典日记）

```json
{
  "id": "example-diary",
  "name": "示例日记",
  "category": "diary",
  "canvas": {
    "width": 1080,
    "height": 1527,
    "background": "#fbfaf6",
    "pattern": "lines",
    "pattern_color": "rgba(160,150,130,0.20)",
    "pattern_spacing": 36
  },
  "slots": [
    {
      "id": "date",
      "type": "text",
      "x": 80, "y": 120, "w": 560, "h": 55,
      "default": "2026年7月5日  星期日",
      "style": {
        "font": {
          "family": "serif",
          "size": 30,
          "color": "#a89888",
          "letter_spacing": 3
        }
      }
    },
    {
      "id": "body",
      "type": "text",
      "x": 80, "y": 331, "w": 920, "h": 1150,
      "default": "今天天气很好，阳光从窗纱里透进来...",
      "style": {
        "font": {
          "family": "serif",
          "size": 36,
          "color": "#4a4030",
          "line_height": 2.0
        }
      }
    }
  ],
  "decorations": [
    {
      "type": "sticker",
      "id": "leaf",
      "x": 870, "y": 50,
      "w": 100, "h": 100,
      "rotation": 15,
      "src": "stickers/leaf.svg"
    }
  ]
}
```

## 通过 Python 动态覆盖内容

```python
from shouzhang.templates import TemplateRegistry
reg = TemplateRegistry()
reg.load_dir("templates/builtin")

doc = reg.instantiate("example-diary", content={
    "date": "2026年7月6日  星期一",
    "body": "今天下雨了..."
})
```
