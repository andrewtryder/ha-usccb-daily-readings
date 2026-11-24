#!/usr/bin/env python3
"""Generate Home Assistant brand assets for USCCB Daily Readings."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = REPO_ROOT / "custom_components" / "usccb_daily_readings" / "brand"
SVG_PATH = BRAND_DIR / "icon.svg"
LOGO_TITLE = "USCCB Daily Readings for Home Assistant"


def _rsvg_convert() -> str:
    """Return the rsvg-convert binary path."""
    for candidate in (
        shutil.which("rsvg-convert"),
        "/opt/homebrew/bin/rsvg-convert",
        "/usr/bin/rsvg-convert",
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    msg = "rsvg-convert is required (e.g. brew install librsvg or apt install librsvg2-bin)"
    raise SystemExit(msg)


def _raster_svg(size: int) -> Image.Image:
    """Rasterize the master SVG to a square RGBA image."""
    binary = _rsvg_convert()
    with tempfile.NamedTemporaryFile(suffix=".png") as handle:
        output = Path(handle.name)
        subprocess.run(
            [
                binary,
                "-w",
                str(size),
                "-h",
                str(size),
                str(SVG_PATH),
                "-o",
                str(output),
            ],
            check=True,
            capture_output=True,
        )
        return Image.open(output).convert("RGBA")


def _make_icon(size: int) -> Image.Image:
    """Return a square icon at the requested size."""
    return _raster_svg(size)


def _load_font(
    size: int, bold: bool = False
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a readable sans-serif font, falling back to Pillow default."""
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _wrap_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int
) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _make_logo(icon: Image.Image, canvas_height: int) -> Image.Image:
    """Build a horizontal logo with the icon and project title."""
    icon_size = round(canvas_height * 0.82)
    icon_mark = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

    font_size = max(18, round(canvas_height * 0.11))
    font = _load_font(font_size, bold=True)

    probe = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(probe)
    text_area = round(canvas_height * 2.2)
    lines = _wrap_text(draw, LOGO_TITLE, font, text_area)
    line_heights = [
        draw.textbbox((0, 0), line, font=font)[3]
        - draw.textbbox((0, 0), line, font=font)[1]
        for line in lines
    ]
    text_height = sum(line_heights) + 8 * (len(lines) - 1)
    text_width = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines)

    padding = round(canvas_height * 0.12)
    canvas_width = padding + icon_size + padding + text_width + padding
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))

    icon_y = (canvas_height - icon_size) // 2
    canvas.alpha_composite(icon_mark, (padding, icon_y))

    text_x = padding + icon_size + padding
    text_y = (canvas_height - text_height) // 2
    draw = ImageDraw.Draw(canvas)
    y = text_y
    for line, line_height in zip(lines, line_heights, strict=True):
        draw.text((text_x, y), line, fill="#822d3e", font=font)
        y += line_height + 8

    return canvas


def main() -> None:
    """Generate icon and logo PNG assets from icon.svg."""
    if not SVG_PATH.is_file():
        msg = f"Missing master SVG: {SVG_PATH}"
        raise SystemExit(msg)

    assets = {
        "icon.png": _make_icon(256),
        "icon@2x.png": _make_icon(512),
    }
    assets["logo.png"] = _make_logo(assets["icon.png"], 256)
    assets["logo@2x.png"] = _make_logo(assets["icon@2x.png"], 512)

    BRAND_DIR.mkdir(parents=True, exist_ok=True)
    for filename, image in assets.items():
        path = BRAND_DIR / filename
        image.save(path, "PNG", optimize=True)
        print(f"Wrote {path} ({image.width}x{image.height})")


if __name__ == "__main__":
    main()
