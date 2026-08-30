"""実際のGUIを起動して取扱説明書用の画面資料を生成する。"""

from __future__ import annotations

import sys
import time
import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageGrab, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import build_application


OUTPUT = Path("docs/media")
OUTPUT.mkdir(parents=True, exist_ok=True)


def pump(root: tk.Tk, seconds: float) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        root.update()
        time.sleep(0.1)


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
    return image.crop(bbox) if bbox else image


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

for key, value in {
    "aoa_min": "-20", "aoa_max": "20", "aos_min": "-20", "aos_max": "20",
    "aoa_points": "5", "aos_points": "5", "tip_offset_x": "100", "tip_offset_y": "10",
    "hold_time_s": "1", "feed_rate": "100", "x_min": "-1000", "x_max": "1000",
    "y_min": "-1000", "y_max": "1000", "z_min": "-180", "z_max": "180",
    "a_min": "-720", "a_max": "720",
}.items():
    app._widget_vars[key].set(value)
app._on_gui_input_changed()
frames.append(capture(root, "02-input-valid"))
pump(root, 3.0)

app._on_simulate()
pump(root, 1.0)
frames.append(capture(root, "03-simulation-start"))
pump(root, 5.0)
frames.append(capture(root, "04-simulation-progress"))

output = OUTPUT / "sample-output.nc"
app._on_generate_gcode(str(output))
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
