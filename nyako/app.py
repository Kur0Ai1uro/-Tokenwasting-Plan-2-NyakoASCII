"""打开 Nyako ASCII 的本地页面。"""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

import webview
from PIL import Image

from nyako.convert import bitmap_to_ascii
from nyako.presets import PRESET_NAMES, resolve_charset
from nyako.text_render import DECORATIONS, FONT_CHOICES, ArtError, render_text


def _root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent.parent


class Api:
    def __init__(self) -> None:
        self.image: Image.Image | None = None

    def options(self) -> dict:
        return {
            "fonts": list(FONT_CHOICES),
            "decorations": [{"label": label, "id": name or ""} for label, name in DECORATIONS],
            "presets": list(PRESET_NAMES),
        }

    def choose_image(self) -> dict:
        paths = webview.windows[0].create_file_dialog(
            webview.FileDialog.OPEN,
            directory=os.path.expanduser("~"),
            file_types=("图片 (*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp)", "所有文件 (*.*)"),
        )
        if not paths:
            return {"ok": False, "cancelled": True, "name": ""}
        path = paths[0]
        try:
            with Image.open(path) as opened:
                opened.load()
                self.image = opened.copy()
        except Exception:
            self.image = None
            return {"ok": False, "cancelled": False, "name": ""}
        return {"ok": True, "cancelled": False, "name": os.path.basename(path)}

    def render(self, payload: dict) -> dict:
        try:
            art = self._render(payload or {})
        except ArtError as exc:
            return {"ok": False, "art": "", "message": str(exc), "columns": 0, "rows": 0}
        except Exception as exc:
            return {"ok": False, "art": "", "message": f"生成失败：{exc}", "columns": 0, "rows": 0}
        lines = art.splitlines() if art else []
        columns = max((len(line) for line in lines), default=0)
        return {
            "ok": True,
            "art": art,
            "message": "",
            "columns": columns,
            "rows": len(lines),
        }

    def copy_text(self, text: str) -> dict:
        _copy_unicode(text or "")
        return {"ok": True}

    def save_text(self, text: str) -> dict:
        if not text:
            return {"ok": False}
        paths = webview.windows[0].create_file_dialog(
            webview.FileDialog.SAVE,
            directory=os.path.expanduser("~"),
            save_filename="nyako.txt",
            file_types=("文本文件 (*.txt)",),
        )
        if not paths:
            return {"ok": False, "cancelled": True}
        path = paths[0]
        if not path.lower().endswith(".txt"):
            path += ".txt"
        body = text if text.endswith("\n") else text + "\n"
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
        return {"ok": True}

    def _render(self, payload: dict) -> str:
        if payload.get("mode") == "text":
            return render_text(
                str(payload.get("text") or ""),
                font=str(payload.get("font") or "standard"),
                decoration=str(payload.get("decoration") or "") or None,
                space=int(payload.get("space") or 0),
            )
        if self.image is None:
            return ""
        return bitmap_to_ascii(
            self.image,
            columns=int(payload.get("columns") or 100),
            charset=resolve_charset(str(payload.get("charset") or ""), str(payload.get("preset") or "中")),
            invert=bool(payload.get("invert")),
            brightness=float(payload.get("brightness") or 1),
            contrast=float(payload.get("contrast") or 1),
            aspect=float(payload.get("aspect") or 0.5),
        )


def _copy_unicode(text: str) -> None:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_int
    user32.EmptyClipboard.argtypes = []
    user32.CloseClipboard.argtypes = []
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    if not user32.OpenClipboard(None):
        raise OSError("无法打开剪贴板")
    try:
        user32.EmptyClipboard()
        data = text.encode("utf-16-le") + b"\0\0"
        handle = kernel32.GlobalAlloc(0x0002, len(data))
        locked = kernel32.GlobalLock(handle)
        if not handle or not locked:
            raise OSError("无法写入剪贴板")
        ctypes.memmove(locked, data, len(data))
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(13, handle):
            raise OSError("无法写入剪贴板")
    finally:
        user32.CloseClipboard()


def main() -> None:
    page = (_root() / "web" / "index.html").resolve().as_uri()
    icon = _root() / "assets" / "nyako.ico"
    webview.create_window("Nyako ASCII", url=page, js_api=Api(), width=1080, height=700, min_size=(880, 620))
    webview.start(icon=str(icon) if icon.is_file() else None)
