# MyAnimeList To Refract

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python 3](https://img.shields.io/badge/python-3-blue.svg)

**English** | [Português](README.pt.md)

Converts your MyAnimeList anime list into the "TV Time Liberator" format that [Refract](https://getrefract.app/)'s TV Time import accepts — for anyone who, like me, lost their TV Time data when it shut down.

## Why: TV Time earned a spot in the Top 10 anime betrayals

Every anime saga has its unforgettable betrayal — the best friend turned villain out of nowhere. This time it wasn't fiction.

I'd used TV Time since July 16, 2020 — the app kept the exact date, and I, a stats junkie, knew it by heart. I lost everything I'd been tracking, like most people: 331 followed shows, 4928 likes, who knows how many hours of `time_spent`. Very proudly logged, I might add.

I felt betrayed: 15 days' notice isn't enough, and an in-app notification is no way to shut down a platform with a massive community. I went looking for my data just 3 days after the shutdown — and the official GDPR portal (`gdpr.tvtime.com`) already had dead DNS. Years of history, gone.

This repository is the record of my effort (Plans A–D) to recover as much as possible, so I wouldn't have to log everything again from scratch — because that's what's going to happen, since I'm a stats junkie.

## At least I have MAL

### What it accepts

MyAnimeList's official anime export (`https://myanimelist.net/panel.php?go=export`, "Anime List") — anyone can grab theirs, even without ever having had a TV Time account.

### What it produces

The **"TV Time Liberator"** format — the same schema Refract's official Chrome extension produced while TV Time was still up, and which Refract's "TV Time" import still accepts even without that extension:

- `tvtime-series-<today>.json` — followed shows + watched episodes
- `tvtime-movies-<today>.json` — watched movies

The exact schema came from the open-source converter [jeremy-albinet/tvtime-to-refract-converter](https://github.com/jeremy-albinet/tvtime-to-refract-converter), which documents it from a real TV Time GDPR export.

Along the way, it solves a real problem: MAL gives each season of an anime its own id (e.g. "Attack on Titan" and "Attack on Titan Season 2" are separate entries), but TV Time/TheTVDB treat the whole show as a single entry with multiple seasons. The script merges the right entries using the community mapping [Fribb/anime-lists](https://github.com/Fribb/anime-lists). Full detail in [docs/mal-import](docs/mal-import/).

### What you need before starting

You don't need to know how to code, but you need two things on your computer:

1. **Python 3** — Mac and Linux usually already have it. To check, open a terminal (see how below) and type:

   ```bash
   python3 --version
   ```

   If you see `Python 3.x.x`, you're set. If you get an error like "command not found", install it from [python.org/downloads](https://www.python.org/downloads/) (on Windows, check the **"Add Python to PATH"** box during install — that's the most common thing people miss).

2. **This repository, downloaded** — you don't need `git`. Go to [github.com/singelodux/mal_to_refract](https://github.com/singelodux/mal_to_refract), click the green **Code → Download ZIP** button, and unzip the folder anywhere.

### How to open a terminal in the project folder

- **Windows**: inside the unzipped folder, hold Shift and right-click an empty space → "Open PowerShell window here" (or "Open in Terminal").
- **Mac**: right-click the folder → Services → "New Terminal at Folder". (If that option isn't there, open Terminal normally, type `cd` and drag the folder into the window.)
- **Linux**: right-click inside the folder in your file manager → "Open in Terminal".

### How to run it

```bash
# 1. Export your anime list at https://myanimelist.net/panel.php?go=export
#    (logged in) → "Anime List" → download the .xml or .xml.gz

# 2. Put that file inside the private/mal/ folder (inside the project folder)

# 3. In the terminal opened in the project folder, run:
python3 mal_to_refract.py

# 4. The result (2 .json files) shows up in the private/output/ folder
```

### How to import into Refract

1. Open Refract → Settings/Import → pick the **"TV Time"** import option.
2. When it asks for files, select the two `.json` files from `private/output/` (one is `tvtime-series-<date>.json`, the other `tvtime-movies-<date>.json`).
3. Confirm the import — Refract shows how many shows/movies it recognized.

## Privacy

The script runs entirely on your computer — it doesn't send anything anywhere, except the one-time, public download of the [Fribb/anime-lists](https://github.com/Fribb/anime-lists) mapping (`anime-list-full.json`, third-party anime data, not yours).

Everything personal (your MAL export, the generated files) lives in `private/`, which is outside version control (see `.gitignore`) — only each subfolder's `README.md` is versioned, as a guide to where things go. See [Repo structure](#repo-structure) below.

## Repo structure

| Path | Contents |
| --- | --- |
| [`docs/`](docs/) | documented results for each plan (public, no personal data) |
| [`docs/resources/`](docs/resources/) | third-party notes, sample data, `tvtime_recover.py` |
| [`mal_to_refract.py`](mal_to_refract.py) | the script, at the repo root |
| `private/` | personal data, exports and real results (outside the public repo, see `.gitignore`) |
| `private/mal/` | raw MyAnimeList exports |
| `private/output/` | real results generated by the scripts on my data |

## My attempts: Plans A–D

| Plan | Result | Detail |
| --- | --- | --- |
| **A** — unrooted Android cache | ❌ Dead end — `adb backup` blocked for third-party apps since Android 12 | [docs/unrooted-android](docs/unrooted-android/) |
| **B** — browser storage | ❌ Dead end — valid session saved locally, but the backend is completely shut down | [docs/browser-storage](docs/browser-storage/) |
| **C** — rebuild the list via MAL | ✅ Works — that's the `mal_to_refract.py` above | [docs/mal-import](docs/mal-import/) |
| **D** — log everything again | 🤷 Only what's left over — most of it was already on MAL too, just missing movies and shows | — |

Hope this helped somehow.

## License

[MIT](./LICENSE)
