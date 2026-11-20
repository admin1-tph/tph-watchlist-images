"""Render a TPH design (.dc.html) to PNG at the size of its root element (e.g. 1080x1350 or 1080x1080).

Usage:
    python3 tools/render.py <design.dc.html> <output.png>

Image src values in the design may be:
  - repo-relative paths such as ../assets/tph-bg.png (resolved from the design file's folder), or
  - canvas blob URLs (/_blob/<id>) for the four known TPH Watchlist assets.
Fonts (Anton, Montserrat 600-900) are installed from npm (@fontsource) on first run.
Needs Python Playwright and a Chrome/Chromium binary.
"""
import asyncio
import os
import pathlib
import re
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
ASSETS = REPO / "assets"
BLOBS = {
    "c94bf306e7ec21e9899696e581960d8c": "tph-bg.png",
    "f65ff0444a68225d9c8f625d55695d4d": "tph-logo.png",
    "1c3e508f66ba97f4f0cdafdf4c3b3fc8": "tph-app.png",
    "0bd1c004ec34788b70736c9eff45ad3d": "tph-qr.png",
}
FONT_DIR = pathlib.Path(os.environ.get("TPH_FONT_DIR", "/tmp/tph-fonts"))


def ensure_fonts():
    base = FONT_DIR / "node_modules" / "@fontsource"
    if not (base / "anton").exists():
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["npm", "i", "--silent", "--prefix", str(FONT_DIR),
                        "@fontsource/anton", "@fontsource/montserrat"], check=True)
    faces = f"@font-face{{font-family:Anton;src:url(file://{base}/anton/files/anton-latin-400-normal.woff2)}}"
    for w in (500, 600, 700, 800, 900):
        faces += (f"@font-face{{font-family:Montserrat;font-weight:{w};"
                  f"src:url(file://{base}/montserrat/files/montserrat-latin-{w}-normal.woff2)}}")
    return faces


def chrome_path():
    for c in ("google-chrome", "chromium", "chromium-browser"):
        p = shutil.which(c)
        if p:
            return p
    return None


def build_page(src: pathlib.Path) -> str:
    html = src.read_text(encoding="utf-8")
    body = html.split("<x-dc>")[1].split("</x-dc>")[0]
    body = re.sub(r"<helmet>.*?</helmet>", "", body, flags=re.S)

    def fix(m):
        val = m.group(1)
        b = re.match(r"/_blob/([0-9a-f]+)$", val)
        if b:
            name = BLOBS.get(b.group(1))
            if not name:
                raise SystemExit(f"Unknown canvas image {val}: add it to assets/ and BLOBS")
            p = ASSETS / name
        elif val.startswith(("http:", "https:", "data:", "file:")):
            return m.group(0)
        else:
            p = (src.parent / val).resolve()
        if not p.exists():
            raise SystemExit(f"Missing image file: {p}")
        return f'src="file://{p}"'

    body = re.sub(r'src="([^"]+)"', fix, body)
    faces = ensure_fonts()
    return ("<!doctype html><html><head><meta charset='utf-8'><style>" + faces +
            "body{margin:0;font-family:Montserrat,sans-serif;background:#eef0f2}</style></head><body>"
            + body + "</body></html>")


async def render(src, out):
    from playwright.async_api import async_playwright
    page_html = build_page(pathlib.Path(src).resolve())
    tmp = pathlib.Path("/tmp/tph-render-page.html")
    tmp.write_text(page_html, encoding="utf-8")
    async with async_playwright() as p:
        kw = {}
        cp = chrome_path()
        if cp:
            kw["executable_path"] = cp
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        await pg.goto(f"file://{tmp}")
        w, h = await pg.evaluate("(()=>{const r=document.body.firstElementChild.getBoundingClientRect();return [Math.round(r.width),Math.round(r.height)]})()")
        await pg.set_viewport_size({"width": w, "height": h})
        await pg.evaluate("document.fonts.ready")
        broken = await pg.evaluate("[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src)")
        if broken:
            raise SystemExit(f"Images failed to load: {broken}")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=out, clip={"x": 0, "y": 0, "width": w, "height": h})
        await b.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    asyncio.run(render(sys.argv[1], sys.argv[2]))
    print("rendered", sys.argv[2])
