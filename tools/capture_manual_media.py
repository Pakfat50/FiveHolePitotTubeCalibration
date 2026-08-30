"""実際のGUIを起動して取扱説明書用の画面資料を生成する。"""

from __future__ import annotations

import sys
import time
import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageGrab
import pyautogui

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import build_application


OUTPUT = Path("docs/media")
OUTPUT.mkdir(parents=True, exist_ok=True)


pyautogui.PAUSE = 0.15


def pump(root: tk.Tk, seconds: float) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        root.update()
        time.sleep(0.1)


def widget_center(widget) -> tuple[int, int]:
    """Tkウィジェットの画面上の中心座標を返す。"""
    widget.update_idletasks()
    return (
        widget.winfo_rootx() + widget.winfo_width() // 2,
        widget.winfo_rooty() + widget.winfo_height() // 2,
    )


def type_into(root: tk.Tk, widget, value: str) -> None:
    """画面上の入力欄をクリックし、キーボード入力で値を置き換える。"""
    pyautogui.click(*widget_center(widget))
    pyautogui.press("home")
    pyautogui.keyDown("shift")
    pyautogui.press("end")
    pyautogui.keyUp("shift")
    pyautogui.press("backspace")
    pyautogui.write(value)
    pump(root, 0.2)


def click_widget(root: tk.Tk, widget) -> None:
    """画面上のボタンをマウスクリックする。"""
    pyautogui.click(*widget_center(widget))
    pump(root, 0.5)


def remove_edge_black(image: Image.Image) -> Image.Image:
    """画面端から連続する黒い余白を白で置換する。"""
    image = image.convert("RGB")
    width, height = image.size
    pixels = image.load()
    visited: set[tuple[int, int]] = set()
    stack = [(x, y) for x in range(width) for y in (0, height - 1)]
    stack.extend((x, y) for y in range(height) for x in (0, width - 1))
    while stack:
        x, y = stack.pop()
        if (x, y) in visited or not (0 <= x < width and 0 <= y < height):
            continue
        visited.add((x, y))
        r, g, b = pixels[x, y]
        if max(r, g, b) > 32:
            continue
        pixels[x, y] = (255, 255, 255)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return image


def crop_black_border(image: Image.Image) -> Image.Image:
    """仮想ディスプレイ外側の黒領域を除去する。"""
    image = remove_edge_black(image)
    background = Image.new("RGB", image.size, "white")
    bbox = ImageChops.difference(image, background).getbbox()
    image = image.crop(bbox) if bbox else image

    # Matplotlib/Tkの端に残る暗色の余白行・列を除去する。
    while image.height > 1:
        dark = sum(max(image.getpixel((x, image.height - 1))) <= 32 for x in range(image.width))
        if dark <= image.width * 0.01:
            break
        image = image.crop((0, 0, image.width, image.height - 1))
    while image.width > 1:
        dark = sum(max(image.getpixel((image.width - 1, y))) <= 32 for y in range(image.height))
        if dark <= image.height * 0.01:
            break
        image = image.crop((0, 0, image.width - 1, image.height))
    return image


def capture(root: tk.Tk, name: str) -> Image.Image:
    root.update()
    image = crop_black_border(ImageGrab.grab())
    image.save(OUTPUT / f"{name}.png")
    return image


def make_overview(frames: list[Image.Image]) -> None:
    """操作の各段階を1枚にまとめる。"""
    width = 600
    tiles = []
    for index, frame in enumerate(frames):
        tile = frame.convert("RGB")
        tile.thumbnail((width, 420))
        canvas = Image.new("RGB", (width, 460), "white")
        canvas.paste(tile, ((width - tile.width) // 2, 32))
        ImageDraw.Draw(canvas).text((12, 8), f"Step {index + 1}", fill="black")
        tiles.append(canvas)
    overview = Image.new("RGB", (width * 2, 460 * 3), "#eeeeee")
    for index, tile in enumerate(tiles):
        overview.paste(tile, ((index % 2) * width, (index // 2) * 460))
    overview.save(OUTPUT / "getting-started-overview.png")


root = tk.Tk()
root.option_add("*font", "{IPAGothic} 10")
for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkCaptionFont", "TkSmallCaptionFont"):
    tkfont.nametofont(name).configure(family="IPAGothic")
app = build_application(root)
root.geometry("1200x900")
root.update()
root.update()
frames: list[Image.Image] = []

frames.append(capture(root, "01-launch"))
pump(root, 2.0)

# 入力欄を順番にクリックし、実際のキーボード入力で設定値を入力する。
values = {
    "aoa_min": "-20", "aoa_max": "20", "aos_min": "-20", "aos_max": "20",
    "aoa_points": "5", "aos_points": "5", "tip_offset_x": "100", "tip_offset_y": "10",
    "hold_time_s": "1", "feed_rate": "100", "x_min": "-1000", "x_max": "1000",
    "y_min": "-1000", "y_max": "1000", "z_min": "-180", "z_max": "180",
    "a_min": "-720", "a_max": "720",
}
for key, value in values.items():
    type_into(root, app._entry_widgets[key], value)
frames.append(capture(root, "02-input-valid"))
pump(root, 2.0)

# シミュレーションボタンを実際にクリックする。
click_widget(root, app.simulation_button)
pump(root, 1.0)
frames.append(capture(root, "03-simulation-start"))
pump(root, 5.0)
frames.append(capture(root, "04-simulation-progress"))

# シミュレーション画面を閉じ、メイン画面のGコード生成ボタンをクリックする。
pyautogui.hotkey("alt", "f4")
pump(root, 1.0)
output = Path("sample-output.nc")
root.after(
    1000,
    lambda: (
        pyautogui.press("home"),
        pyautogui.keyDown("shift"),
        pyautogui.press("end"),
        pyautogui.keyUp("shift"),
        pyautogui.press("backspace"),
        pyautogui.write(output.name),
        pyautogui.press("enter"),
    ),
)
click_widget(root, app.gcode_button)
pump(root, 1.0)
frames.append(capture(root, "05-gcode-generated"))
pump(root, 2.0)

# 5枚の実画面をつないだ、操作の流れを示す約30秒のGIF。
durations = [5000, 5000, 6000, 8000, 6000]
frames = [crop_black_border(frame) for frame in frames]
make_overview(frames)
canvas_size = (max(frame.width for frame in frames), max(frame.height for frame in frames))
normalized = []
for frame in frames:
    canvas = Image.new("RGB", canvas_size, "white")
    canvas.paste(frame, ((canvas_size[0] - frame.width) // 2, (canvas_size[1] - frame.height) // 2))
    normalized.append(canvas)
normalized[0].save(
    OUTPUT / "getting-started.gif",
    save_all=True,
    append_images=normalized[1:],
    duration=durations,
    loop=0,
)
output.unlink(missing_ok=True)
root.destroy()
