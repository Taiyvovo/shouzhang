# 字体系统

98+ 字体、覆盖 5 种语言。字体文件放在 `src/font/`，`FontRegistry` 递归扫描 `.ttf` 和 `.otf`。

## 基本概念

**通用字体**（无需 `.ttf` 文件）——直接写在模板里，系统自备：

| 名称 | 说明 |
|---|---|
| `serif` | 衬线体（默认宋体/宋体类） |
| `sans-serif` | 无衬线体（默认黑体/微软雅黑类） |
| `monospace` | 等宽体 |

**自定义字体**（需要 `.ttf` 文件）——`FontRegistry` 扫描 `src/font/`，自动识别字族和字重。

## 字体命名规则

模板里使用的 `family` 名称由 `FontRegistry` 从文件名自动解析：

| 文件名 | 解析后的 family | 字重 | 斜体 |
|---|---|---|---|
| `NotoSansSC-Regular.ttf` | `Noto Sans SC` | 400 | ❌ |
| `NotoSansSC-Bold.ttf` | `Noto Sans SC` | 700 | ❌ |
| `NotoSansSC-Light.ttf` | `Noto Sans SC` | 300 | ❌ |
| `Lora-Italic.ttf` | `Lora` | 400 | ✅ |
| `Lora-BoldItalic.ttf` | `Lora` | 700 | ✅ |

**命名规则**：`Family-Regular.ttf` / `Family-Bold.ttf` / `Family-BoldItalic.ttf`

## 可用字体一览

### 中文字体

| Family 名称 | 语言 | 字重范围 |
|---|---|---|
| `Noto Sans SC` | 简体中文 | Thin ~ Black (100~900) |
| `Noto Serif SC` | 简体中文 | ExtraLight ~ Black (200~900) |
| `华康娃娃体-非商` | 简体中文 | Regular |
| `OPPO Sans` | 简体中文 | Regular |

### 日文字体

| Family 名称 | 语言 | 字重范围 |
|---|---|---|
| `Noto Sans JP` | 日本語 | Thin ~ Black (100~900) |
| `Noto Serif JP` | 日本語 | Variable + static |
| `Yuyu` | 日本語（手写） | Regular |
| `WDXLLubrifont JPN` | 日本語（装饰） | Regular |

### 英文字体

| Family 名称 | 风格 | 字重范围 |
|---|---|---|
| `Google Sans` | 现代无衬线 | Regular ~ Black |
| `Lora` | 优雅衬线 | Regular ~ Bold + Italic |
| `Roboto Slab` | 粗衬线 | Thin ~ Black (100~900) |
| `Bebas Neue` | 大写展示 | Regular |
| `Cherry Bomb One` | 圆润 playful | Regular |
| `Fascinate Inline` | 镂空复古 | Regular |

### 像素字体（Fusion Pixel）

3 种字号 × 5 种语言 = 15 个变体：

| Family 名称 | 语言 | 原生字号 | 类型 |
|---|---|---|---|
| `Fusion Pixel 8 px Proportional ZH Hans` | 简体中文 | 8px | 比例 |
| `Fusion Pixel 8 px Proportional ZH Hant` | 繁體中文 | 8px | 比例 |
| `Fusion Pixel 8 px Proportional JA` | 日本語 | 8px | 比例 |
| `Fusion Pixel 8 px Proportional KO` | 한국어 | 8px | 比例 |
| `Fusion Pixel 8 px Proportional Latin` | English | 8px | 比例 |
| `Fusion Pixel 10 px Monospaced ZH Hans` | 简体中文 | 10px | 等宽 |
| `Fusion Pixel 10 px Monospaced ZH Hant` | 繁體中文 | 10px | 等宽 |
| `Fusion Pixel 10 px Monospaced JA` | 日本語 | 10px | 等宽 |
| `Fusion Pixel 10 px Monospaced KO` | 한국어 | 10px | 等宽 |
| `Fusion Pixel 10 px Monospaced Latin` | English | 10px | 等宽 |
| `Fusion Pixel 12 px Proportional ZH Hans` | 简体中文 | 12px | 比例 |
| `Fusion Pixel 12 px Proportional ZH Hant` | 繁體中文 | 12px | 比例 |
| `Fusion Pixel 12 px Proportional JA` | 日本語 | 12px | 比例 |
| `Fusion Pixel 12 px Proportional KO` | 한국어 | 12px | 比例 |
| `Fusion Pixel 12 px Proportional Latin` | English | 12px | 比例 |

## 模板中使用字体

```json
{
  "style": {
    "font": {
      "family": "Noto Sans SC",
      "size": 36,
      "weight": 700
    }
  }
}
```

直接写 family 名称即可，大小写不敏感（`"noto sans sc"` = `"Noto Sans SC"`）。

## 渲染策略

| 场景 | 后端 | 说明 |
|---|---|---|
| 通用字体（serif/sans-serif） | resvg | 快，系统字体 |
| 自定义字体 | Edge headless | SVG 内嵌 `@font-face` 声明，浏览器渲染 |
| PNG 输出 | Edge / resvg | 根据字体自动选择 |
| SVG 输出 | 直接写入 | `@font-face` 声明保留在 SVG 中，用户用浏览器打开即可看到正确字体 |

## 注意事项

- **含空格的字体名**：`Noto Sans SC` 这种带空格的 family 名，SVG 编译器会自动在 `font-family` 属性外加单引号（`'Noto Sans SC'`），避免浏览器按空格拆词
- **字重匹配**：`FontRegistry.find(family, weight)` 会找与其最接近的字重文件。比如请求 `weight=600` 但没有 SemiBold 文件时，会返回 Bold（700）或 Medium（500）
- **像素字体字号**：推荐使用原生字号的整数倍（8px→16px/24px，10px→20px/30px，12px→24px/36px），否则浏览器会抗锯齿导致模糊

## 添加自己的字体

1. 把 `.ttf` / `.otf` 文件放在 `src/font/` 下任意子目录
2. 文件名遵循 `Family-Weight.ttf` 格式（如 `MyFont-Bold.ttf`）
3. 模板中用 `"family": "MyFont"` 引用
4. `FontRegistry.scan()` 会自动识别
