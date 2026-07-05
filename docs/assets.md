# 素材参考

所有素材路径相对于 `assets/` 目录。

## 贴纸（Stickers）

模板中 `src` 路径省略 `assets/` 前缀。例如 `assets/stickers/moon.svg` 写作 `"stickers/moon.svg"`。

### 根目录（5 个）

| src | 描述 |
|---|---|
| `stickers/cloud.svg` | 白云 |
| `stickers/flower.svg` | 粉色六瓣花 |
| `stickers/leaf.svg` | 绿叶带茎脉 |
| `stickers/moon.svg` | 月牙带陨坑 |
| `stickers/star.svg` | 金色五角星 |

### emotion/ — 表情（4 个）

| src | 描述 |
|---|---|
| `stickers/emotion/happy.svg` | 黄色笑脸 |
| `stickers/emotion/love.svg` | 粉色爱心眼 |
| `stickers/emotion/calm.svg` | 蓝色平静脸 |
| `stickers/emotion/sleepy.svg` | 米色困倦脸 |

### item/ — 物品（6 个）

| src | 描述 |
|---|---|
| `stickers/item/camera.svg` | 复古相机 |
| `stickers/item/coffee.svg` | 咖啡杯带热气 |
| `stickers/item/book.svg` | 绿色书本 |
| `stickers/item/heart.svg` | 红心 |
| `stickers/item/balloon.svg` | 红色气球 |
| `stickers/item/cola.svg` | 红色易拉罐 |

### plant/ — 植物（4 个）

| src | 描述 |
|---|---|
| `stickers/plant/cactus.svg` | 盆栽仙人掌 |
| `stickers/plant/mushroom.svg` | 红色蘑菇带斑点 |
| `stickers/plant/low-grass.svg` | 矮草丛 |
| `stickers/plant/tall-grass.svg` | 高草丛 |

### weather/ — 天气（4 个）

| src | 描述 |
|---|---|
| `stickers/weather/sunny.svg` | 太阳 |
| `stickers/weather/cloudy.svg` | 多云 |
| `stickers/weather/rainy.svg` | 下雨 |
| `stickers/weather/snow.svg` | 雪花 |

## 背景（Backgrounds）

```json
{ "type": "background", "svg": "kraft" }
```

| svg | 描述 | 尺寸 |
|---|---|---|
| `"kraft"` | 牛皮纸纹理（噪点 + 暗角 + 虚线边框） | 1080×1527 |
| `"mint"` | 薄荷绿网格 + 渐变顶栏 + 内边框 | 1080×1527 |

## 胶带（Tapes）

| src | 描述 |
|---|---|
| `tapes/washi-1.svg` | 米色和纸胶带（斜线纹理 + 虚线边） |

## 自定义素材

把 `.svg` 文件放在 `assets/` 下任意子目录，模板中用相对路径引用：

```json
{ "type": "sticker", "src": "stickers/my-sticker.svg" }
```

## 图片格式

图片元素支持嵌入或文件路径：

```json
// 文件路径
{ "type": "image", "src": "photos/sunset.png" }

// Base64 内嵌
{ "type": "image", "src": "data:image/png;base64,iVBOR..." }
```

支持的图片格式：PNG、JPEG、WebP、GIF（自动转为 base64 内嵌到 SVG）。
