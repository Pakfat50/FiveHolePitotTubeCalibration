"""実際のGUIを起動して取扱説明書用の画面資料を生成する。"""

from __future__ import annotations

import sys
import time
import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageGrab
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


def annotation_font(size: int):
    """注記用の日本語フォントを取得する。"""
    candidates = (
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
        "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def annotate_frame(image: Image.Image, stage: str) -> Image.Image:
    """GIF用に操作対象を赤枠と注記で示す。"""
    image = image.convert("RGB")
    draw = ImageDraw.Draw(image)
    font = annotation_font(max(22, image.width // 52))
    red = "#d7191c"

    def label(x: int, y: int, text: str) -> None:
        bounds = draw.textbbox((0, 0), text, font=font)
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        x = max(8, min(x, image.width - width - 24))
        y = max(8, min(y, image.height - height - 18))
        draw.rounded_rectangle(
            (x - 8, y - 5, x + width + 8, y + height + 5),
            radius=7,
            fill=red,
        )
        draw.text((x, y), text, fill="white", font=font)

    def box(left: int, top: int, right: int, bottom: int, text: str, label_x: int, label_y: int) -> None:
        draw.rounded_rectangle((left, top, right, bottom), radius=8, outline=red, width=5)
        label(label_x, label_y, text)

    if stage == "launch":
        label(18, 14, "① ツールを起動")
    elif stage == "input":
        box(8, 48, 368, 612, "② 条件値を入力", 18, 14)
    elif stage == "simulation":
        # シミュレーション画面の状態表示と進捗バーを強調する。
        box(685, 454, 1134, 744, "③ シミュレーションを確認", 698, 420)
        box(695, 687, 1035, 730, "進捗", 900, 650)
    elif stage == "gcode":
        box(8, 810, 1192, 897, "④ Gコードを生成", 18, 778)
        box(1055, 842, 1192, 897, "クリック", 1000, 778)
    return image


def add_gif_padding(image: Image.Image, padding: int = 24) -> Image.Image:
    """GIFの画面端に余白を追加し、ボタンの見切れを防ぐ。"""
    canvas = Image.new("RGB", (image.width + padding * 2, image.height + padding * 2), "white")
    canvas.paste(image, (padding, padding))
    return canvas


root = tk.Tk()
root.option_add("*font", "{IPAGothic} 10")
for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkCaptionFont", "TkSmallCaptionFont"):
    tkfont.nametofont(name).configure(family="IPAGothic")
app = build_application(root)
# 実操作でシミュレーションを開始した後、開始直後と途中の2画面を
# 取得できるよう、キャプチャ時だけ再生時間を30秒へ延長する。
original_simulation_start = app.simulation_controller.start


def start_capture_simulation(plan, duration_s=10.0):
    original_simulation_start(plan, duration_s=30.0)


app.simulation_controller.start = start_capture_simulation
root.geometry("1200x900")
root.update()
root.update()
frames: list[Image.Image] = []

frames.append(capture(root, "01-launch"))
pump(root, 2.0)

# 入力欄を順番にクリックし、実際のキーボード入力で設定値を入力する。
values = {
    "aoa_min": "-20", "aoa_max": "20", "aos_min": "-20", "aos_max": "20",
    "aoa_points": "15", "aos_points": "15", "tip_offset_x": "200", "tip_offset_y": "200",
    "hold_time_s": "1", "feed_rate": "100", "x_min": "-100", "x_max": "100",
    "y_min": "-100", "y_max": "100", "z_min": "-45", "z_max": "45",
    "a_min": "-90", "a_max": "90",
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
# Tkのウィンドウマネージャー差異を避け、表示専用のシミュレーション窓だけを閉じる。
simulation_view = app.simulation_controller.view
simulation_figure = getattr(simulation_view, "figure", None)
simulation_manager = getattr(getattr(simulation_figure, "canvas", None), "manager", None)
simulation_window = getattr(simulation_manager, "window", None)
if simulation_window is not None:
    simulation_window.destroy()
pump(root, 1.0)
output = Path("sample-output.nc")
# キャプチャでは保存ダイアログの環境差を避けるため保存先だけ固定し、
# Gコード生成ボタンは通常どおり画面上のマウスクリックで実行する。
import gui
gui.filedialog.asksaveasfilename = lambda **_kwargs: str(output)

click_widget(root, app.gcode_button)
pump(root, 1.0)
frames.append(capture(root, "05-gcode-generated"))
pump(root, 2.0)

# 5枚の実画面へ注記と赤枠を追加し、操作の流れを示す約30秒のGIFにする。
durations = [5000, 5000, 6000, 8000, 6000]
stages = ["launch", "input", "simulation", "simulation", "gcode"]
annotated = [
    add_gif_padding(annotate_frame(crop_black_border(frame), stage))
    for frame, stage in zip(frames, stages)
]
canvas_size = (max(frame.width for frame in annotated), max(frame.height for frame in annotated))
normalized = []
for frame in annotated:
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
