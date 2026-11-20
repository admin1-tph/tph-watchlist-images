# tph-watchlist-images

Public image host for the weekly **TPH Watchlist** post on the TRADERS PH Facebook page.
Buffer downloads each week's image from this repository by its raw link.

## Layout

- `watchlist/`: one finished PNG per week, named `TPH-Watchlist-YYYY-MM-DD.png` (the Friday the week ends).
- `assets/`: the four fixed images in the design: `tph-bg.png`, `tph-logo.png`, `tph-app.png`, `tph-qr.png`.
- `template/TPHWatchlist-reference.dc.html`: the current design, with image paths pointing at `assets/`.
- `tools/render.py`: renders a design file to a 1080×1350 PNG (`python3 tools/render.py <design> <out.png>`).

## Image link format

`https://raw.githubusercontent.com/admin1-tph/tph-watchlist-images/main/watchlist/<file>.png`

Everything here is public. Only put finished, ready-to-post images in it.
