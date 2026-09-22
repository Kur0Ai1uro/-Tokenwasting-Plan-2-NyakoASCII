"""灰度字符集。字符串从左到右表示从暗到亮。"""

PRESET_NAMES = ("细", "中", "粗")

# 经典细字符坡度是从亮到暗，这里反过来，保证左暗右亮。
_FINE_LIGHT_TO_DARK = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

PRESETS = {
    "细": _FINE_LIGHT_TO_DARK[::-1],
    "中": "@%#*+=-:. ",
    "粗": "@#+=. ",
}


def resolve_charset(custom: str, preset_name: str) -> str:
    """自定义字符串非空时优先使用；否则退回预设。"""
    if custom.strip():
        return custom
    return PRESETS.get(preset_name, PRESETS["中"])
