"""WCAG contrast check for tokens.json. Run: python design-system/bad-habits/contrast.py"""
import json, pathlib, sys
tokens = json.loads((pathlib.Path(__file__).parent / "tokens.json").read_text())

def lum(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def ratio(a, b):
    a, b = lum(a), lum(b); return (max(a, b) + 0.05) / (min(a, b) + 0.05)

# (foreground, background, minimum): 4.5 for text, 3 for non-text UI
PAIRS = [("ink", "bg", 4.5), ("ink", "surface", 4.5), ("inkMuted", "bg", 4.5), ("inkMuted", "surface", 4.5),
         ("inkMuted", "surfaceSunken", 4.5), ("primary", "surface", 4.5), ("onPrimary", "primary", 4.5),
         ("behindText", "surface", 4.5), ("danger", "surface", 4.5), ("primary", "primarySoft", 3),
         ("primary", "track", 3), ("behind", "track", 3), ("miss", "surface", 3)]
failed = False
for mode, pal in tokens["color"].items():
    print(f"-- {mode}")
    for fg, bg, m in PAIRS:
        r = ratio(pal[fg]["$value"], pal[bg]["$value"]); ok = r >= m; failed |= not ok
        print(f"{fg:>11} on {bg:<13} {r:5.2f}  {'OK' if ok else 'FAIL'} (min {m})")
sys.exit(1 if failed else 0)
