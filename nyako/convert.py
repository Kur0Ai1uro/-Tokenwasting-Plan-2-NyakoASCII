"""把位图采样成灰度 ASCII。"""

from PIL import Image, ImageEnhance, ImageOps

MAX_COLUMNS = 300


def bitmap_to_ascii(
    image: Image.Image,
    *,
    columns: int = 100,
    charset: str = "@%#*+=-:. ",
    invert: bool = False,
    brightness: float = 1.0,
    contrast: float = 1.0,
    aspect: float = 0.5,
) -> str:
    """按列数和字符宽高比采样。charset 从左到右为从暗到亮。"""
    if not charset:
        charset = "@%#*+=-:. "

    image = _normalize(image)
    image = ImageEnhance.Brightness(image).enhance(_clamp(brightness, 0.0, 3.0))
    image = ImageEnhance.Contrast(image).enhance(_clamp(contrast, 0.0, 3.0))
    image = image.convert("L")
    if invert:
        image = ImageOps.invert(image)

    columns = max(1, min(MAX_COLUMNS, int(columns)))
    aspect = _clamp(aspect, 0.2, 1.5)
    width, height = image.size
    if width < 1 or height < 1:
        return ""

    rows = max(1, round(height / width * columns * aspect))
    image = image.resize((columns, rows), Image.Resampling.LANCZOS)

    pixels = list(image.getdata())
    span = len(charset) - 1
    lines: list[str] = []
    for y in range(rows):
        start = y * columns
        row = pixels[start : start + columns]
        if span <= 0:
            lines.append(charset[0] * columns)
            continue
        lines.append("".join(charset[min(span, int(pixel / 255 * span))] for pixel in row))
    return "\n".join(lines)


def _normalize(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode == "RGBA" or (image.mode == "P" and "transparency" in image.info):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    max_side = 1600
    width, height = image.size
    longest = max(width, height)
    if longest > max_side:
        scale = max_side / longest
        image = image.resize(
            (max(1, int(width * scale)), max(1, int(height * scale))),
            Image.Resampling.LANCZOS,
        )
    return image


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))
