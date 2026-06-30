"""Install official WOP App logo assets with transparent background."""
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMAGES_DIR = os.path.join(BASE_DIR, "app", "static", "images")

# Official WOP App logo provided by ministry (black background source)
DEFAULT_SOURCE = os.path.join(IMAGES_DIR, "wop-logo-source.png")
CURSOR_SOURCE = os.path.join(
    os.path.expanduser("~"),
    ".cursor", "projects", "c-Users-user-Desktop-Men-and-Women-of-passion-and-purpose",
    "assets",
    "c__Users_user_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_wop_image-4f8fcaef-1abe-4f91-a4bc-edd81f02a9bb.png",
)

PURPLE = (90, 24, 154, 255)
GOLD = (212, 175, 55, 255)
WHITE = (255, 255, 255, 255)


def resolve_source_path():
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        return sys.argv[1]
    if os.path.isfile(DEFAULT_SOURCE):
        return DEFAULT_SOURCE
    if os.path.isfile(CURSOR_SOURCE):
        return CURSOR_SOURCE
    raise FileNotFoundError(
        "WOP logo source not found. Pass path: python scripts/install_wop_logo.py <source.png>"
    )


def remove_black_background(img, threshold=45):
    """Remove solid black background while preserving gold logo edges."""
    img = img.convert("RGBA")
    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            luminance = max(r, g, b)
            if luminance <= threshold:
                pixels[x, y] = (r, g, b, 0)
            elif luminance <= threshold + 35:
                # Soft edge anti-aliasing on dark fringe pixels
                alpha = int(255 * (luminance - threshold) / 35)
                pixels[x, y] = (r, g, b, min(255, alpha))

    return img


def trim_transparent(img):
    bbox = img.getbbox()
    if bbox:
        return img.crop(bbox)
    return img


def save_logo_assets(source_path):
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Preserve master source in project for regeneration
    master = os.path.join(IMAGES_DIR, "wop-logo-source.png")
    if os.path.abspath(source_path) != os.path.abspath(master):
        shutil.copy2(source_path, master)

    img = Image.open(source_path)
    logo = trim_transparent(remove_black_background(img))

    logo_path = os.path.join(IMAGES_DIR, "logo.png")
    logo.save(logo_path, "PNG", optimize=True)
    print(f"Created {logo_path} ({logo.size[0]}x{logo.size[1]}, transparent)")

    # Favicon sizes
    for size, name in [(32, "favicon.png"), (180, "apple-touch-icon.png"), (16, "favicon-16.png")]:
        icon = logo.copy()
        icon.thumbnail((size, size), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        offset = ((size - icon.size[0]) // 2, (size - icon.size[1]) // 2)
        canvas.paste(icon, offset, icon)
        path = os.path.join(IMAGES_DIR, name)
        canvas.save(path, "PNG", optimize=True)
        print(f"Created {path}")

    create_og_share(logo)
    print("WOP App logo installation complete.")


def create_og_share(logo):
    w, h = 1200, 630
    bg = Image.new("RGB", (w, h), PURPLE[:3])
    draw = ImageDraw.Draw(bg)
    draw.rectangle([0, h - 8, w, h], fill=GOLD[:3])

    display = logo.copy()
    display.thumbnail((220, 220), Image.Resampling.LANCZOS)
    x = 80
    y = (h - display.size[1]) // 2
    bg.paste(display, (x, y), display)

    try:
        title_font = ImageFont.truetype("arialbd.ttf", 48)
        sub_font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    draw.text((320, h // 2 - 55), "WOPP App", fill=GOLD[:3], font=title_font)
    draw.text((320, h // 2 + 5), "Men and Women of", fill=WHITE[:3], font=sub_font)
    draw.text((320, h // 2 + 45), "Passion and Purpose", fill=WHITE[:3], font=sub_font)

    path = os.path.join(IMAGES_DIR, "og-share.png")
    bg.save(path, "PNG", optimize=True)
    print(f"Created {path}")


if __name__ == "__main__":
    save_logo_assets(resolve_source_path())
