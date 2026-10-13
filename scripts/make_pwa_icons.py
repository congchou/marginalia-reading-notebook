"""Generate self-contained PNG icons for the offline iPhone PWA."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1] / "docs" / "pwa"
FONT = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"


def make_icon(size: int, name: str) -> None:
    scale = size / 512
    image = Image.new("RGB", (size, size), "#f5f0e7")
    draw = ImageDraw.Draw(image)
    inset = round(28 * scale)
    draw.rounded_rectangle((inset, inset, size - inset, size - inset), radius=round(110 * scale), fill="#674728")
    font = ImageFont.truetype(FONT, round(310 * scale))
    box = draw.textbbox((0, 0), "M", font=font)
    x = (size - (box[2] - box[0])) / 2 - box[0]
    y = (size - (box[3] - box[1])) / 2 - box[1] - round(11 * scale)
    draw.text((x, y), "M", font=font, fill="#fff8e9")
    draw.rounded_rectangle((round(337 * scale), round(337 * scale), round(373 * scale), round(421 * scale)), radius=round(6 * scale), fill="#d7af73")
    image.save(ROOT / name, optimize=True)


if __name__ == "__main__":
    make_icon(192, "icon-192.png")
    make_icon(512, "icon-512.png")
    make_icon(180, "apple-touch-icon.png")
