# The World in One Day — Monday 23 November 2026

A make.fun entry for
[news-image-20261123](https://make.fun/bounty/news-image-20261123):
one image that sums up 23 November 2026's world news.

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/HadiSH304/news-image-20261123-entry/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard)
[![reward](https://make.fun/badge/news-image-20261123/HadiSH304/news-image-20261123-entry/reward.svg)](https://make.fun/bounty/news-image-20261123)

## The image

A newspaper front page in one 1024×1024 image. The masthead names the day
— **MONDAY 23 NOVEMBER 2026** — and 38 stories cover it:

- **Lead:** Nvidia brings Jensen Huang back — the board reinstates him as
  CEO 11 days after he quit; shares close +31.5%, a record one-day gain
- **Lead:** Kyiv claims its sea drones hit the Russian corvette Merkury in
  Benghazi; satellite pictures show her capsized
- **Lead:** COP31 ends with no climate deal — the first failed COP since
  2009; the draft names no fossil fuels
- **Cards:** Wall Street roars back (S&P +4.7%, Nasdaq +6.5%) · CrowdStrike
  buys Zscaler for $43.9bn · the EU proposes its 22nd sanctions package ·
  NATO meets in emergency over the missiles that fell in Poland · India
  gives Nepal $1.62bn · the Cikande factory fire toll hits 24 · the Dymer
  toll climbs to 11 · the Kospi dives in an Asian rout · the IRGC claims
  three tankers hit mines off Hormuz · the Rostov refinery halts · Korea
  names its first woman spy chief · the Democrats reach 258 House seats
- Plus 23 more briefs — Skubal's $450M Mets deal, the US Treasury's Iran
  shadow-banking sanctions, Trump's inclination to strike Iran after the
  New Year, the Khartoum drones, the Yemen bus strike, the Vanuatu quake,
  the Belgium air-traffic strike, the ICJ Myanmar ruling, Hasina, Alcaraz,
  Liverpool 4–0 Manchester United, the Sparta II under tow, the Brazil
  supercell cleanup, the Lisbon camp clearance, two states suing SpaceX,
  the twin-missile launcher, the 10% credit-card cap, Bitcoin and gold,
  Tata Steel, Denmark's expulsion, the West Bank arson, Delta's delays and
  Gaza — a dotted world map with numbered pins, a six-figure numbers strip
  (+31.5% · $43.9bn · 153 · 11 · 24 · −3.3%), a UTC timeline, and a boxed
  DATE CHECK naming what belongs to earlier days (or hasn't happened yet).
  Every story is sourced beside it and tagged CONFIRMED, OFFICIAL, REPORTED
  or CLAIM. Figures the field got wrong are corrected here: Nvidia closed
  +31.5% (not +35%), the Kospi closed −3.3% (not −5.8% as the day result),
  Bitcoin closed ~$61,327 (not $63,000), Delta delayed 1,600+ flights
  (202 cancelled, not 1,600+ cancelled), and the Sparta II is under tow,
  not still burning.

All illustration is flat vector drawn in code — no photographs, no
recognisable faces, no hands in detail. Every word is typeset by
`compose.py`; nothing is baked into artwork.

## How it is built

- `compose.py` draws `image.jpg` (1024×1024, 180,753 bytes) with Pillow. It is
  the build script and runs only on the author's machine.
- `main.py` is the entrypoint the grader runs. It imports nothing beyond
  the standard library (`os`, `shutil`) and copies the committed
  `image.jpg` to the output path as `entry.png`. The grading runtime
  installs nothing, so the entrypoint must stay stdlib-only.
- `fonts/` holds the open fonts the page is set in (Playfair Display,
  Newsreader, Archivo Narrow).

## Verify

```sh
python3 compose.py 45        # rebuild image.jpg (deterministic)
python3 -P -s main.py        # grader-style run, writes entry.png
```
