"""下载开源字体到 src/font/（自由商用许可，不含华康娃娃体等非商字体）"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "src" / "font"

FONTS_DIRTY = []

SOURCES = {
    ("Noto_Sans_SC", "NotoSansSC-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/notosanssc/static/NotoSansSC-Regular.ttf",
    ("Noto_Sans_SC", "NotoSansSC-Bold.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/notosanssc/static/NotoSansSC-Bold.ttf",
    ("Noto_Serif_SC", "NotoSerifSC-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/notoserifsc/static/NotoSerifSC-Regular.ttf",
    ("Noto_Serif_SC", "NotoSerifSC-Bold.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/notoserifsc/static/NotoSerifSC-Bold.ttf",
    ("Noto_Sans_JP", "NotoSansJP-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/notosansjp/static/NotoSansJP-Regular.ttf",
    ("Noto_Sans_JP", "NotoSansJP-Bold.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/notosansjp/static/NotoSansJP-Bold.ttf",
    ("Noto_Serif_JP", "NotoSerifJP-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/notoserifjp/static/NotoSerifJP-Regular.ttf",
    ("Lora_EN", "Lora-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-Regular.ttf",
    ("Lora_EN", "Lora-Bold.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-Bold.ttf",
    ("Lora_EN", "Lora-Italic.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/lora/static/Lora-Italic.ttf",
    ("Bebas_Neue_EN", "BebasNeue-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
    ("Cherry_Bomb_One_EN", "CherryBombOne-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/cherrybombone/CherryBombOne-Regular.ttf",
    ("Fascinate_Inline_EN", "FascinateInline-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/fascinateinline/FascinateInline-Regular.ttf",
    ("Roboto_Slab_EN", "RobotoSlab-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/apache/robotoslab/static/RobotoSlab-Regular.ttf",
    ("Roboto_Slab_EN", "RobotoSlab-Bold.ttf"):
        "https://github.com/google/fonts/raw/main/apache/robotoslab/static/RobotoSlab-Bold.ttf",
    ("Yuyu_EN", "Yuyu-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/yujihei/YujiHei-Regular.ttf",
    ("WDXLLubrifont_JPN", "WDXLLubrifontJPN-Regular.ttf"):
        "https://github.com/google/fonts/raw/main/ofl/lacquer/Lacquer-Regular.ttf",
}


def dl(url, dest):
    if dest.exists():
        print(f"  ~ {dest.name} (exists)")
        return
    print(f"  -> {dest.name}")
    try:
        from urllib.request import urlretrieve
        urlretrieve(url, dest)
    except Exception as e:
        print(f"  X FAIL: {e}")
        FONTS_DIRTY.append(str(dest))


def main():
    print("Downloading open-source fonts...\n")
    for (subdir, fname), url in SOURCES.items():
        dest = FONTS / subdir / fname
        dest.parent.mkdir(parents=True, exist_ok=True)
        dl(url, dest)

    print(f"\nDone. {len(SOURCES) - len(FONTS_DIRTY)} fonts downloaded.")
    if FONTS_DIRTY:
        print("Failed:")
        for f in FONTS_DIRTY:
            print(f"  {f}")

    print("""
Missing? Manually download:
  Fusion Pixel → https://github.com/TakWolf/fusion-pixel-font/releases
  华康娃娃体  → (non-commercial, not included)""")

if __name__ == "__main__":
    main()
