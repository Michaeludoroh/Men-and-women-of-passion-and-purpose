"""Generate ministry media assets using the official WOP App logo."""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
IMAGES_DIR = os.path.join(STATIC_DIR, "images")
APP_DIR = os.path.join(IMAGES_DIR, "app")
LOGO_PATH = os.path.join(IMAGES_DIR, "logo.png")
LOGO_SOURCE_PATH = os.path.join(IMAGES_DIR, "wop-logo-source.png")

PURPLE = (90, 24, 154, 255)
GOLD = (212, 175, 55, 255)
WHITE = (255, 255, 255, 255)
PURPLE_DARK = (60, 15, 110, 255)
GOLD_DARK = (184, 150, 46, 255)


def ensure_dirs():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(APP_DIR, exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, "uploads", "leaders"), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, "uploads", "gallery"), exist_ok=True)


def ensure_logo_assets():
    """Install official WOP logo if missing."""
    if os.path.isfile(LOGO_PATH):
        return
    installer = os.path.join(BASE_DIR, "scripts", "install_wop_logo.py")
    source = LOGO_SOURCE_PATH if os.path.isfile(LOGO_SOURCE_PATH) else None
    cmd = [sys.executable, installer]
    if source:
        cmd.append(source)
    subprocess.run(cmd, check=True)


def load_wop_logo(max_height):
    """Load official transparent WOP logo scaled to max height."""
    ensure_logo_assets()
    logo = Image.open(LOGO_PATH).convert("RGBA")
    ratio = max_height / logo.size[1]
    new_size = (int(logo.size[0] * ratio), max_height)
    return logo.resize(new_size, Image.Resampling.LANCZOS)


def paste_logo(canvas, logo, position, bg_color=None):
    """Paste transparent logo onto RGB or RGBA canvas."""
    if canvas.mode != "RGBA" and bg_color is not None:
        layer = Image.new("RGBA", logo.size, bg_color)
        layer.paste(logo, (0, 0), logo)
        rgb_logo = Image.new("RGB", logo.size, bg_color[:3])
        rgb_logo.paste(layer, mask=layer.split()[3])
        canvas.paste(rgb_logo, position)
    else:
        canvas.paste(logo, position, logo)


def create_sermon_placeholder():
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (60, 15, 110))
    draw = ImageDraw.Draw(img)

    for i in range(0, w, 40):
        draw.line([(i, 0), (i, h)], fill=(90, 24, 154), width=1)

    logo = load_wop_logo(120)
    paste_logo(img, logo, ((w - logo.size[0]) // 2, (h - logo.size[1]) // 2 - 30), PURPLE)

    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except OSError:
        font = ImageFont.load_default()

    draw.text((w // 2, h // 2 + 90), "MWPP Sermon", fill=GOLD, font=font, anchor="mm")

    path = os.path.join(IMAGES_DIR, "sermon-placeholder.jpg")
    img.save(path, "JPEG", quality=90)
    print(f"Created {path}")


def create_leader_placeholder():
    w, h = 400, 500
    img = Image.new("RGB", (w, h), (245, 240, 255))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([20, 20, w - 20, h - 20], radius=20, fill=PURPLE)
    logo = load_wop_logo(80)
    paste_logo(img, logo, ((w - logo.size[0]) // 2, (h - logo.size[1]) // 2), PURPLE)

    path = os.path.join(IMAGES_DIR, "leader-placeholder.jpg")
    img.save(path, "JPEG", quality=90)
    print(f"Created {path}")


def create_app_screenshot(index, label):
    w, h = 390, 844
    img = Image.new("RGB", (w, h), (30, 10, 55))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([10, 10, w - 10, h - 10], radius=40, fill=(45, 15, 80))
    draw.rounded_rectangle([20, 60, w - 20, h - 30], radius=20, fill=(90, 24, 154))

    logo = load_wop_logo(56)
    paste_logo(img, logo, ((w - logo.size[0]) // 2, 120), PURPLE)

    try:
        font = ImageFont.truetype("arial.ttf", 22)
        small = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
        small = ImageFont.load_default()

    draw.text((w // 2, 210), "WOP App", fill=GOLD, font=font, anchor="mm")
    draw.text((w // 2, 250), label, fill=WHITE, font=small, anchor="mm")

    for i, color in enumerate([GOLD_DARK[:3], PURPLE[:3], (123, 44, 191)]):
        y = 320 + i * 90
        draw.rounded_rectangle([40, y, w - 40, y + 70], radius=12, fill=color)

    path = os.path.join(APP_DIR, f"screenshot-{index}.png")
    img.save(path, "PNG")
    print(f"Created {path}")


def create_qr_placeholder():
    size = 256
    img = Image.new("RGB", (size, size), WHITE)
    draw = ImageDraw.Draw(img)

    draw.rectangle([8, 8, size - 8, size - 8], outline=PURPLE, width=3)

    cell = 12
    for row in range(0, size - 40, cell):
        for col in range(0, size - 40, cell):
            if (row + col) % (cell * 2) == 0:
                draw.rectangle(
                    [20 + col, 20 + row, 20 + col + cell - 2, 20 + row + cell - 2],
                    fill=PURPLE if (row * col) % 3 == 0 else GOLD_DARK[:3],
                )

    for ox, oy in [(20, 20), (size - 80, 20), (20, size - 80)]:
        draw.rectangle([ox, oy, ox + 56, oy + 56], outline=PURPLE, width=4)
        draw.rectangle([ox + 12, oy + 12, ox + 44, oy + 44], fill=PURPLE)

    logo = load_wop_logo(40)
    paste_logo(img, logo, ((size - logo.size[0]) // 2, (size - logo.size[1]) // 2), WHITE)

    path = os.path.join(APP_DIR, "qr-placeholder.png")
    img.save(path, "PNG")
    print(f"Created {path}")


def main():
    ensure_dirs()
    ensure_logo_assets()
    create_sermon_placeholder()
    create_leader_placeholder()
    create_qr_placeholder()
    for i, label in enumerate(
        ["Sermons & Prayer", "Events & Gallery", "School & Community"], start=1
    ):
        create_app_screenshot(i, label)
    print("All ministry assets generated successfully.")


if __name__ == "__main__":
    main()
