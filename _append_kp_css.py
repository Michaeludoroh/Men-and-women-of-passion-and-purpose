# Append Kingdom Partner CSS to styles.css if not already present.
from pathlib import Path

css_src = Path(r"C:\Users\user\Desktop\Men and Women of passion and purpose\ministry_project\_kp_partnership.css")
path = Path(r"C:\Users\user\Desktop\Men and Women of passion and purpose\ministry_project\app\static\css\styles.css")

css = css_src.read_text(encoding="utf-8")
# Strip BOM if PowerShell wrote one
if css.startswith("\ufeff"):
    css = css.lstrip("\ufeff")

content = path.read_text(encoding="utf-8")
if ".kp-hero {" in content:
    print("ALREADY_PRESENT")
else:
    with path.open("a", encoding="utf-8") as f:
        f.write("\n" + css)
    print("APPENDED", len(css))

final = path.read_text(encoding="utf-8")
print("FINAL_CHARS", len(final))
print("FINAL_BYTES", path.stat().st_size)
print("---LAST5---")
print("\n".join(final.splitlines()[-5:]))
print("HAS_KP_HERO", ".kp-hero {" in final)
print("HAS_UNSPLASH", "photo-1438232998663" in final)
print("KP_RULE_COUNT", final.count(".kp-"))
