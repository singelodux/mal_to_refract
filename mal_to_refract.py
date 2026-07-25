#!/usr/bin/env python3
"""
mal_to_refract.py
Author:  Singelo Dux
Repo:    https://github.com/singelodux/mal_to_refract
License: MIT

Converts a MyAnimeList XML export into the "TV Time Liberator" format Refract's TV Time import expects (`tvtime-series-<date>.json` + `tvtime-movies-<date>.json`). Full rationale — why this format, its provenance, the MAL/TVDB season-merging problem and how Fribb's mapping solves it, coverage limits, and the "not found" investigation — lives in docs/mal-import/ (README.md / README.en.md). This docstring only covers what's needed to read the code below.

Canonical shapes (fields we don't have from MAL are set to their documented "unknown" value — null/false/"unknown" — matching what the real GDPR parser itself does when TV Time's own export lacks the same data; e.g. episode `name` and per-episode `id.tvdb` are null even in genuine GDPR-derived output, "not present in GDPR export"):

  show  = { uuid, id:{tvdb,imdb}, created_at, title, status, is_favorite,
            seasons: [{ number, is_specials, episodes: [{
              id:{tvdb,imdb}, number, name, special,
              is_watched, watched_at, rewatch_count, watched_count
            }] }] }
  movie = { id:{tvdb,imdb}, uuid, created_at, title, year,
            watched_at, is_watched, is_favorite, rewatch_count }

Field mapping notes:
  - status: MAL's "Dropped" -> "archived", everything else -> "followed". (These are the only two real values TV Time's own GDPR export uses for a followed show, per parse-gdpr.js — TV Time does NOT encode watching/completed/plan-to-watch at the show level; that's entirely derived from episode-level is_watched/watched_at, which is what this script builds too.)
  - MAL's series_type == "Movie" -> emitted as a movie, not a show+season.
  - episodes 1..my_watched_episodes are marked is_watched (MAL only gives a per-season *count*, not which specific episodes — assumes sequential viewing within a season, which is a season-scoped, much safer assumption than guessing across a whole multi-season show).
  - rewatch_count comes from MAL's my_times_watched (count - 1, floored at 0), applied uniformly to every episode/movie in that entry since MAL doesn't track rewatches per-episode.
  - watched_at (per episode/movie) uses MAL's my_finish_date, falling back to my_start_date — the closest MAL gets to a real watch timestamp; applied to every episode in that season since MAL has no per-episode date.

Usage:
    python3 mal_to_refract.py [animelist.xml or .xml.gz] [output_dir]

With no arguments, reads whichever single MAL export it finds in private/mal/ (see private/mal/README.md) and writes to private/output/ (see private/output/README.md) — matching the private/ convention documented in docs/mal-import/.

Needs anime-list-full.json from Fribb/anime-lists next to this script (or pass its path as a 3rd argument) — downloaded automatically on first run if missing. It's ~7.5MB and updates periodically upstream; don't commit your cached copy to a public repo, just re-download it when needed.
"""

import gzip
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MAL_DIR = os.path.join(REPO_ROOT, "private", "mal")
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "private", "output")
MAPPING_URL = "https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-full.json"
MAPPING_CACHE = os.path.join(REPO_ROOT, "anime-list-full.json")


def ensure_mapping():
    if not os.path.exists(MAPPING_CACHE):
        print("Downloading anime id mapping from Fribb/anime-lists (~7.5MB, one-time)...", file=sys.stderr)
        urllib.request.urlretrieve(MAPPING_URL, MAPPING_CACHE)
    with open(MAPPING_CACHE, encoding="utf-8") as f:
        entries = json.load(f)
    mapping = {}
    for e in entries:
        mal_id = e.get("mal_id")
        if not mal_id:
            continue
        tvdb_id = e.get("tvdb_id")
        season = (e.get("season") or {}).get("tvdb")
        imdb_ids = e.get("imdb_id") or []
        imdb_id = imdb_ids[0] if imdb_ids else None
        # Fribb only tags an explicit `season.tvdb` when a mal_id maps to a
        # season other than the show's first: One Piece, Pokemon and Bleach
        # each have dozens of movie/special/later-arc mal_ids at season 2+
        # (or 0 for specials), while the *original* mal_id — the one that IS
        # season 1 — carries no `season` key at all. Verified across the
        # whole dataset: no tvdb_id ever has both a season-less entry and
        # another entry explicitly at season 1, so a missing season next to
        # a present tvdb_id always means "this is season 1", never genuine
        # ambiguity. Discarding the tvdb_id whenever season was missing (the
        # old behavior here) silently dropped correct, unambiguous ids for
        # well-known shows — see docs/mal-import/ for the investigation.
        mapping[mal_id] = {
            "tvdb_id": tvdb_id,
            "season": (season or 1) if tvdb_id else None,
            "imdb_id": imdb_id,
        }
    return mapping


def find_default_input():
    all_files = os.listdir(DEFAULT_MAL_DIR) if os.path.isdir(DEFAULT_MAL_DIR) else []
    candidates = [f for f in all_files if f.endswith(".xml") or f.endswith(".xml.gz")]
    if not candidates:
        sys.exit(
            "No .xml/.xml.gz found in %s — export your anime list from "
            "https://myanimelist.net/panel.php?go=export and put it there "
            "(see private/mal/README.md), or pass a path explicitly."
            % DEFAULT_MAL_DIR
        )

    # MAL's export filenames always start with "animelist" (mangalist exports
    # use the same directory/extension but aren't anime data) — prefer those.
    anime_candidates = [f for f in candidates if f.lower().startswith("animelist")]
    pool = anime_candidates or candidates

    if len(pool) > 1:
        # Likely the same export kept as both .xml and .xml.gz — take whichever
        # is newest rather than making the user spell out a path every time.
        pool.sort(key=lambda f: os.path.getmtime(os.path.join(DEFAULT_MAL_DIR, f)), reverse=True)
        print("Multiple candidates in %s (%s) — using the most recently modified: %s"
              % (DEFAULT_MAL_DIR, ", ".join(sorted(pool)), pool[0]), file=sys.stderr)

    return os.path.join(DEFAULT_MAL_DIR, pool[0])


def load_xml(path):
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return ET.parse(f)
    return ET.parse(path)


def parse_mal_date_space(value):
    """MAL date ('YYYY-MM-DD' or '0000-00-00') -> 'YYYY-MM-DD HH:MM:SS' or None,
    matching model.js's normalizeDate() output format for episode watched_at."""
    if not value or value == "0000-00-00":
        return None
    return value + " 00:00:00"


def parse_mal_date_iso(value):
    """Same, but ISO form ('YYYY-MM-DDT00:00:00Z'), matching normalizeDateIso()
    for created_at / movie watched_at."""
    if not value or value == "0000-00-00":
        return None
    return value + "T00:00:00Z"


def epcode_watched_at(finish_date, start_date):
    return parse_mal_date_space(finish_date) or parse_mal_date_space(start_date)


def main():
    in_path = sys.argv[1] if len(sys.argv) > 1 else find_default_input()
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    if len(sys.argv) > 3:
        global MAPPING_CACHE
        MAPPING_CACHE = sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)

    mal_to_tvdb = ensure_mapping()

    tree = load_xml(in_path)
    root = tree.getroot()

    # tvdb_id -> list of MAL entries (one per season) to merge into one show.
    tvdb_groups = {}
    unmapped_shows = []
    movies = []

    for anime in root.findall("anime"):
        mal_id = int(anime.findtext("series_animedb_id"))
        mal_status = anime.findtext("my_status")
        watched_count = int(anime.findtext("my_watched_episodes") or 0)
        aired_count = int(anime.findtext("series_episodes") or 0)
        times_watched = int(anime.findtext("my_times_watched") or 0)
        rewatch_count = max(times_watched - 1, 0)
        finish_date = anime.findtext("my_finish_date")
        start_date = anime.findtext("my_start_date")
        name = anime.findtext("series_title")
        series_type = anime.findtext("series_type")

        mapping = mal_to_tvdb.get(mal_id) or {"tvdb_id": None, "season": None, "imdb_id": None}
        is_watched = mal_status != "Plan to Watch"

        if series_type == "Movie":
            movies.append({
                "id": {"tvdb": mapping["tvdb_id"], "imdb": mapping["imdb_id"]},
                "uuid": None,
                "created_at": None,
                "title": name,
                "year": None,
                "watched_at": parse_mal_date_iso(finish_date) or parse_mal_date_iso(start_date),
                "is_watched": is_watched,
                "is_favorite": False,
                "rewatch_count": rewatch_count if is_watched else 0,
            })
            continue

        entry = {
            "name": name,
            "mal_status": mal_status,
            "watched_count": watched_count,
            "aired_count": aired_count,
            "rewatch_count": rewatch_count,
            "watched_at": epcode_watched_at(finish_date, start_date),
            "imdb_id": mapping["imdb_id"],
        }

        if mapping["tvdb_id"]:
            entry["season"] = mapping["season"]
            tvdb_groups.setdefault(mapping["tvdb_id"], []).append(entry)
        else:
            unmapped_shows.append(entry)

    shows = []

    def build_episodes(season_num, watched_count, watched_at, rewatch_count):
        return [
            {
                "id": {"tvdb": None, "imdb": None},
                "number": n,
                "name": None,
                "special": season_num == 0,
                "is_watched": True,
                "watched_at": watched_at,
                "rewatch_count": rewatch_count,
                "watched_count": rewatch_count + 1,
            }
            for n in range(1, watched_count + 1)
        ]

    for tvdb_id, entries in tvdb_groups.items():
        entries.sort(key=lambda e: e["season"])
        any_dropped = any(e["mal_status"] == "Dropped" for e in entries)
        imdb_id = next((e["imdb_id"] for e in entries if e["imdb_id"]), None)
        seasons = [
            {
                "number": e["season"],
                "is_specials": e["season"] == 0,
                "episodes": build_episodes(e["season"], e["watched_count"], e["watched_at"], e["rewatch_count"]),
            }
            for e in entries if e["watched_count"] > 0
        ]
        shows.append({
            "uuid": None,
            "id": {"tvdb": tvdb_id, "imdb": imdb_id},
            "created_at": None,
            "title": entries[0]["name"],
            "status": "archived" if any_dropped else "followed",
            "is_favorite": False,
            "seasons": seasons,
        })

    for e in unmapped_shows:
        seasons = [{
            "number": 1,
            "is_specials": False,
            "episodes": build_episodes(1, e["watched_count"], e["watched_at"], e["rewatch_count"]),
        }] if e["watched_count"] > 0 else []
        shows.append({
            "uuid": None,
            "id": {"tvdb": None, "imdb": e["imdb_id"]},
            "created_at": None,
            "title": e["name"],
            "status": "archived" if e["mal_status"] == "Dropped" else "followed",
            "is_favorite": False,
            "seasons": seasons,
        })

    shows.sort(key=lambda s: (s["title"] or "").lower())
    movies.sort(key=lambda m: (m["title"] or "").lower())

    today = date.today().isoformat()
    series_path = os.path.join(out_dir, "tvtime-series-%s.json" % today)
    movies_path = os.path.join(out_dir, "tvtime-movies-%s.json" % today)

    with open(series_path, "w", encoding="utf-8") as f:
        json.dump(shows, f, indent=2, ensure_ascii=False)
    with open(movies_path, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

    watched_episodes = sum(
        1 for s in shows for se in s["seasons"] for ep in se["episodes"] if ep["is_watched"]
    )
    print("Wrote %s (%d shows, %d watched episodes)" % (series_path, len(shows), watched_episodes))
    print("Wrote %s (%d movies)" % (movies_path, len(movies)))
    print("  merged into TVDB shows: %d   kept without a TVDB match: %d"
          % (len(tvdb_groups), len(unmapped_shows)))


if __name__ == "__main__":
    main()
