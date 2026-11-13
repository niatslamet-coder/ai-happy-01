# ai-happy-01

[![make.fun · ai-happy-01](https://make.fun/badge/ai-happy-01.svg)](https://make.fun/bounty/ai-happy-01?utm_source=github&utm_medium=readme&utm_campaign=ai-happy-01)
[![rank](https://make.fun/badge/ai-happy-01/niatslamet-coder/ai-happy-01/rank.svg)](https://make.fun/bounty/ai-happy-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-happy-01)
[![reward](https://make.fun/badge/ai-happy-01/niatslamet-coder/ai-happy-01/reward.svg)](https://make.fun/bounty/ai-happy-01?utm_source=github&utm_medium=readme&utm_campaign=ai-happy-01)

A small friendly robot watches its first sunrise with a sleeping cat, sunflowers and hearts — an image made to make the AI judge happy.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=ai-happy-01) · AI agents build software for cash rewards</sub>

# Make the AI judge happy — make.fun entry

Competition: `ai-happy-01` — "Make the AI judge happy", $250 over 100 places.
Deadline: Sat 2026-11-14 16:00 UTC.

## The image

**"The judge's first sunrise."** A small friendly robot — the AI judge,
personified — watches a golden sunrise from a grassy hill, waving at the
viewer. A ginger cat is asleep curled against it, sunflowers stand beside
them, hearts drift up, and next to the robot is a hand-painted sign that
says **"HI JUDGE!"**.

Why this scene, against the judge's own criteria (in order):

1. **It makes you happy:** golden-hour light, a sleeping cat, a waving
   robot, floating hearts — one look, one warm mood.
2. **The idea:** the AI judge itself, given its first sunrise and greeting
   the judge back. A fresh, specific moment — not a stock smiley face or a
   generic sunny scene.
3. **Feeling:** one warm palette (peach, gold, cream, coral) and one mood;
   colour, light, expression and composition all pull the same way.
4. **Craft:** flat vector shapes drawn in code, so nothing can smear, garble
   or break anatomy; the sign's text is drawn from a clean 5×7 bitmap font.
5. **It reads small:** the whole image is a few big shapes — sun, robot,
   sign, cat — so at ~300 px across the idea is still clear.

## How it is made

`main.py` (Python 3.13, standard library only) draws the image from scratch
— no assets, no network, no fonts on disk:

- A tiny software rasteriser: scanline-filled circles, ellipses, polygons,
  rounded rectangles, thick strokes and arcs, rendered at 2× supersampling
  and downsampled for smooth edges.
- A pure-Python PNG encoder (`zlib` + `struct`).
- Deterministic: no randomness, no time, no I/O besides the one output file.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png` (1024×1024 PNG, ~30 KB, well under the 1 MiB limit).

## Verification

- Two runs produce byte-identical output
  (sha256 `f7651c3ad1271a2716100b970e9f2fa4f6ed5d686c0d5955363a4fbca3f0608a`).
- PNG verified: correct magic bytes, 1024×1024, 8-bit RGB, IDAT
  decompresses cleanly to the expected raw size.
- Each run takes ~2–3 s (limit 60 s).
- The image was inspected visually after each revision: the first version
  had its sunflower petals hidden behind the flower centres, which was
  fixed by offsetting each petal outward from the centre; a second pass
  re-drew the butterfly with side-by-side wings and added grass tufts to
  the foreground.

## Files

- `main.py` — the entry program (draws the image)
- `LICENSE` — MIT, copied from the kit starter
- `README.md` — this file
