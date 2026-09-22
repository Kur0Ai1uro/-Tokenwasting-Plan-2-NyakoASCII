"""用 art 库把文字画成设计好的 ASCII 字体。"""

from __future__ import annotations

import unicodedata

from art import DECORATION_NAMES, FONT_NAMES, decor, text2art
from art.errors import artError as LibraryArtError

_FONT_PREFERENCE = (
    "standard",
    "slant",
    "small",
    "big",
    "banner",
    "block",
    "doom",
    "graffiti",
    "cyberlarge",
    "cybermedium",
    "letters",
    "colossal",
    "nancyj",
    "nancyj-fancy",
    "isometric1",
    "isometric2",
    "isometric3",
    "starwars",
    "chunky",
    "avatar",
    "rectangles",
    "roman",
    "speed",
    "epic",
    "shadow",
    "script",
    "caligraphy",
    "rounded",
    "bulbhead",
    "larry3d",
    "poison",
    "soft",
    "stop",
    "weird",
    "digital",
    "gothic",
    "fuzzy",
    "diamond",
    "alpha",
    "thick",
    "thin",
    "wavy",
    "hollywood",
    "lcd",
    "puffy",
    "stampatello",
    "swan",
    "usaflag",
    "whimsy",
    "sub-zero",
    "cricket",
    "crawford",
    "dotmatrix",
    "graceful",
    "ogre",
    "pawp",
    "rammstein",
    "serifcap",
    "smslant",
    "stacey",
    "tombstone",
    "trek",
    "3-d",
    "contessa",
    "merlin1",
    "nvscript",
    "pebbles",
    "drpepper",
    "goofy",
    "maxfour",
    "rozzo",
    "straight",
    "tanja",
    "ticks",
    "ticksslant",
    "twopoint",
    "univers",
    "rowancap",
    "o8",
    "lean",
    "modular",
    "pepper",
    "sblood",
    "smisome1",
    "fourtops",
    "eftiwall",
    "eftipiti",
    "doh",
)

_DECORATION_PREFERENCE = (
    ("无", None),
    ("猫", "cat1"),
    ("猫爪", "cat2"),
    ("爱心", "heart1"),
    ("星星", "star6"),
    ("箭头", "arrow4"),
    ("方块", "block1"),
    ("线条", "line1"),
    ("波浪", "wave6"),
    ("火焰", "flame1"),
)

_KNOWN_FONTS = {name.lower(): name for name in FONT_NAMES}
_KNOWN_DECORATIONS = set(DECORATION_NAMES)

FONT_CHOICES = tuple(name for name in _FONT_PREFERENCE if name.lower() in _KNOWN_FONTS)
DECORATIONS = tuple(
    (label, name)
    for label, name in _DECORATION_PREFERENCE
    if name is None or name in _KNOWN_DECORATIONS
)


class ArtError(Exception):
    """可以展示给用户的生成错误。"""


def render_text(
    text: str,
    font: str = "standard",
    decoration: str | None = None,
    space: int = 0,
) -> str:
    if not str(text).strip():
        return ""

    font_name = _resolve_font(font)
    decoration_name = _resolve_decoration(decoration)
    try:
        rendered = text2art(
            text,
            font=font_name,
            chr_ignore=False,
            decoration=None,
            space=max(0, min(3, int(space))),
        )
    except LibraryArtError as exc:
        message = str(exc)
        suffix = " is invalid."
        if message.endswith(suffix):
            char = message[: -len(suffix)]
            raise ArtError(f"字体「{font_name}」不支持字符「{char}」。") from exc
        raise ArtError("文字生成失败，请换一个字体。") from exc
    rendered = rendered.rstrip("\n")
    if decoration_name:
        rendered = _wrap_decoration(rendered, decoration_name)
    return rendered


def _resolve_font(font: str) -> str:
    if not isinstance(font, str) or not font.strip():
        raise ArtError("请选择一个字体。")
    key = font.strip().lower()
    if key not in _KNOWN_FONTS:
        raise ArtError(f"没有名为「{font.strip()}」的字体。")
    return _KNOWN_FONTS[key]


def _resolve_decoration(decoration: str | None) -> str | None:
    if decoration is None or decoration == "":
        return None
    if decoration not in _KNOWN_DECORATIONS:
        raise ArtError(f"没有名为「{decoration}」的装饰。")
    return decoration


def _display_width(text: str) -> int:
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
    return width


def _wrap_decoration(art: str, name: str) -> str:
    """装饰单独成行，避免库把装饰粘在正文第一行前面。"""
    head, tail = decor(name, both=True)
    lines = art.split("\n")
    width = max((_display_width(line) for line in lines), default=0)

    def block(raw: str) -> list[str]:
        text = str(raw).strip("\n")
        if not text.strip():
            return []
        placed = []
        for line in text.split("\n"):
            gap = width - _display_width(line)
            placed.append((" " * (gap // 2) + line) if gap > 0 else line)
        return placed

    return "\n".join(block(head) + lines + block(tail))
