"""実際のGUIを起動して取扱説明書用の画面資料を生成する。"""

from __future__ import annotations

import sys
import time
import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path

from PIL import Image, ImageGrab

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import build_application


OUTPUT = Path("docs/media")
OUTPUT.mkdir(parents=True, exist_ok=True)


def pump(root: tk.Tk, seconds: float) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        root.update()
        time.sleep(0.1)


def capture(root: tk.Tk, name: str) -> Image.Image:
    root.update()
    image = ImageGrab.grab()
    image.save(OUTPUT / f"{name}.png")
    return image


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
frames[0].save(
    OUTPUT / "getting-started.gif",
    save_all=True,
    append_images=frames[1:],
    duration=durations,
    loop=0,
)
output.unlink(missing_ok=True)
root.destroy()
