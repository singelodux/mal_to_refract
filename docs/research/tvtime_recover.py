#!/usr/bin/env python3
"""
Recover TV Time data from an offline DioCache.db (the app's HTTP response cache).
The cache stores cached JSON API responses in table `cache_dio(key, subKey,
content, ...)`. `key` is a hash of the request URL and `subKey` a hash of the
request options, so the same endpoint appears under one `key` with several
`subKey` snapshots taken at different times. This script does NOT rely on those
hashes: it classifies every cached response by the *shape* of its JSON, then
merges every snapshot together (deduping by show / episode id) so we recover as
much as the cache ever held.
Recovered per show: followed / favorited / watched flags, TV Time's own watch
status (up_to_date / continuing / stopped / not_started_yet / watch_later),
follow & last-watched dates, watched/aired episode counts (where cached), and
the explicit list of watched episodes as SxxEyy codes (where cached).
Output (both written in one run): a clean JSON file plus a matching CSV with the
same per-show data (one row per show; watched_episodes is a single comma-separated
column). The CSV path is the output path with a .csv extension.
Usage:
    python3 tvtime_recover.py [DioCache.db] [output.json]
"""

import csv
import json
import os
import sqlite3
import sys
from collections import defaultdict

DEFAULT_DB = "~/Downloads/DioCache.db"
DEFAULT_OUT = "~/Downloads/tvtime_export.json"

# TV Time's per-show status buckets (found in each follow object's `filter`).
# These three mean the user has actually watched at least one episode.
WATCHED_STATUSES = {"up_to_date", "continuing", "stopped"}
# These two mean followed / saved but not started.
UNWATCHED_STATUSES = {"not_started_yet", "watch_later"}

# Description of every field an item in the "shows" array may carry, emitted
# into the JSON under notes.fields. A field is omitted from a show entry when
# the cache held no value for it. Keys here mirror `key_order` below exactly.
SHOW_FIELD_DOCS = {
    "id": "Numeric show id (TheTVDB series id, as used by TV Time).",
    "name": "Show title.",
    "followed": "true if the show is in your Following list. Every recovered show is followed.",
    "favorited": "true if the show is in your 'Favorite Shows' list.",
    "watched": "true if you have started watching it (status_category up_to_date / continuing / "
               "stopped); false if only followed or saved (not_started_yet / watch_later).",
    "status_category": "TV Time's own per-show status: up_to_date = caught up on every aired "
                       "episode; continuing = watching, in progress; stopped = started then dropped; "
                       "not_started_yet = followed but not begun; watch_later = saved to watch later.",
    "show_status": "Airing status of the show itself: 'Continuing' or 'Ended'.",
    "network": "Network / streamer that airs the show. Present only for shows whose episodes were cached.",
    "country": "Country of origin as an ISO code (e.g. US, GB, IT).",
    "followed_at_date": "When you started following the show, as a full ISO 8601 timestamp (date + "
                        "time, UTC).",
    "last_watched_date": "Your most recent watch activity for the show, as a full ISO 8601 timestamp "
                         "(date + time). Omitted for shows you never watched.",
    "watched_episode_count": "Episodes you have watched (authoritative total). Present only for shows "
                             "whose counts were cached.",
    "aired_episode_count": "Episodes aired to date. Present only where cached.",
    "is_up_to_date": "true if you have watched every episode aired so far.",
    "is_archived": "true if you archived the show in TV Time.",
    "is_for_later": "true if the show is flagged to watch later.",
    "last_watched_episode": "Furthest episode you have watched, as an SxxEyy code. Present only for "
                            "shows with per-episode detail.",
    "watched_episodes": "Individually-recovered watched episodes as SxxEyy codes (a list in JSON; a "
                        "single comma-separated column in the CSV). May be incomplete — see "
                        "watched_episodes_partial.",
    "watched_episodes_partial": "true when the watched_episodes list is smaller than "
                                "watched_episode_count, i.e. the cache only stored some (usually the "
                                "latest) seasons. Absent when the list appears complete.",
    "hashtag": "TV Time social hashtag for the show.",
    "poster": "Poster image URL (TheTVDB).",
    "favorited_at_date": "When you added the show to Favorites, as a full ISO 8601 timestamp (date + "
                         "time, UTC). Present only for favorited shows.",
}


def unwrap(obj):
    """Strip the {"status":"success","data":...} envelope used by many endpoints."""
    if isinstance(obj, dict) and "data" in obj and set(obj.keys()) <= {"status", "data", "message"}:
        return obj["data"]
    return obj


def epcode(season, number):
    """Format a season/episode pair as SxxEyy (e.g. 1,1 -> 'S01E01')."""
    try:
        return "S%02dE%02d" % (int(season), int(number))
    except (TypeError, ValueError):
        return None


def newer(a, b):
    """Return the later of two ISO-ish timestamp strings (None-safe)."""
    if not a:
        return b
    if not b:
        return a
    return a if a >= b else b


def main():
    db_path = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB)
    out_path = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT)
    csv_path = (out_path[:-5] if out_path.endswith(".json") else out_path) + ".csv"

    con = sqlite3.connect(db_path)
    rows = con.execute("SELECT content FROM cache_dio").fetchall()
    con.close()

    user = {}
    shows = {}                       # show_id -> merged record
    follow_seen_at = {}              # show_id -> updated_at of the follow snapshot we trusted
    watched_eps = defaultdict(dict)  # show_id -> {episode_id: (season, number, name, seen_date)}
    favorite_ids = set()
    followed_ids = set()

    def rec(sid):
        return shows.setdefault(int(sid), {"id": int(sid)})

    def set_if_better(d, field, value):
        """Fill a field only if empty; used for stable-ish attributes."""
        if value not in (None, "", []) and not d.get(field):
            d[field] = value

    for (content,) in rows:
        try:
            data = unwrap(json.loads(content))
        except (json.JSONDecodeError, TypeError):
            continue

        # ---- User profile fragments -------------------------------------
        if isinstance(data, dict) and "id" in data and "name" in data:
            if "following_count" in data:
                user.setdefault("id", data["id"]); user["name"] = data["name"]
                user["social_following_count"] = data["following_count"]
            if "follower_count" in data:
                user.setdefault("id", data["id"]); user["name"] = data["name"]
                user["social_follower_count"] = data["follower_count"]
            if "avatar" in data:  # richer profile blob
                user.setdefault("id", data["id"]); user["name"] = data["name"]
                for k in ("is_vip", "is_premium"):
                    if k in data:
                        user[k] = data[k]

        # ---- Favorite lists (favorite-series / favorite-movies) ---------
        if (isinstance(data, dict) and data.get("type") == "list"
                and str(data.get("id", "")).startswith("favorite-")):
            for o in (data.get("objects") or []):
                if data["id"] == "favorite-series" and o.get("id"):
                    sid = o["id"]
                    favorite_ids.add(int(sid))
                    d = rec(sid)
                    set_if_better(d, "name", o.get("name"))
                    set_if_better(d, "show_status", o.get("status"))
                    set_if_better(d, "poster", (o.get("poster") or {}).get("url"))
                    set_if_better(d, "favorited_at", o.get("created_at"))
                    ws = o.get("watch_status") or {}
                    merge_counts(d, ws.get("watched_episode_count"), ws.get("aired_episode_count"),
                                 ws.get("is_up_to_date"), ws.get("is_archived"), ws.get("is_for_later"))
            continue

        # ---- Followed shows list (objects of type "follow") -------------
        if (isinstance(data, dict) and data.get("type") == "list"
                and isinstance(data.get("objects"), list)
                and data["objects"] and data["objects"][0].get("type") == "follow"):
            for o in data["objects"]:
                if o.get("entity_type") != "series":
                    continue
                meta = o.get("meta") or {}
                sid = meta.get("id")
                if not sid:
                    continue
                followed_ids.add(int(sid))
                d = rec(sid)
                set_if_better(d, "name", meta.get("name"))
                set_if_better(d, "country", meta.get("country"))
                set_if_better(d, "hashtag", meta.get("hashtag"))
                if meta.get("is_ended") is not None and not d.get("show_status"):
                    d["show_status"] = "Ended" if meta["is_ended"] else "Continuing"
                # poster from meta.images
                if not d.get("poster"):
                    for img in (meta.get("images") or []):
                        if img.get("type") == "poster" and img.get("url"):
                            d["poster"] = img["url"]; break
                # Trust status_category / dates from the most recently updated snapshot.
                upd = o.get("updated_at")
                if newer(upd, follow_seen_at.get(int(sid))) == upd or int(sid) not in follow_seen_at:
                    follow_seen_at[int(sid)] = upd
                    flt = o.get("filter") or []
                    cat = next((x for x in flt if x != "all"), None)
                    if cat:
                        d["status_category"] = cat
                    wd = next((s.get("value") for s in (o.get("sorting") or [])
                               if s.get("id") == "watch_date"), None)
                    fd = next((s.get("value") for s in (o.get("sorting") or [])
                               if s.get("id") == "follow_date"), None)
                    d["last_watched"] = newer(d.get("last_watched"), wd)
                    set_if_better(d, "followed_at", fd or o.get("created_at"))
            continue

        # ---- Per-user shows grid with watch counts (5B645...) -----------
        if isinstance(data, dict) and isinstance(data.get("shows"), list) and data["shows"] \
                and "watched_episode_count" in data["shows"][0]:
            for s in data["shows"]:
                if not s.get("id"):
                    continue
                d = rec(s["id"])
                set_if_better(d, "name", s.get("name"))
                set_if_better(d, "show_status", s.get("status"))
                set_if_better(d, "poster", (s.get("poster") or {}).get("url"))
                if s.get("is_favorite"):
                    favorite_ids.add(int(s["id"]))
                merge_counts(d, s.get("watched_episode_count"), s.get("aired_episode_count"),
                             s.get("is_up_to_date"), s.get("is_archived"), s.get("is_for_later"))
            continue

        # ---- Episode arrays: keep only episodes actually seen -----------
        if isinstance(data, list) and data and isinstance(data[0], dict) \
                and "season_number" in data[0] and "show" in data[0]:
            for e in data:
                if not e.get("seen"):
                    continue
                sh = e.get("show") or {}
                sid = sh.get("id")
                if not sid or not e.get("id"):
                    continue
                d = rec(sid)
                set_if_better(d, "name", sh.get("name"))
                set_if_better(d, "network", e.get("network"))
                watched_eps[int(sid)][e["id"]] = (
                    e.get("season_number"), e.get("number"), e.get("name"), e.get("seen_date"))
            continue

    # ---- Fold explicit watched episodes into show records ---------------
    for sid, eps in watched_eps.items():
        d = rec(sid)
        codes = sorted({epcode(s, n) for (s, n, _, _) in eps.values() if epcode(s, n)})
        d["watched_episodes"] = codes
        if codes:
            d["last_watched_episode"] = codes[-1]
        # Latest actual watch timestamp from episode seen_dates, if newer.
        for (_, _, _, sd) in eps.values():
            if sd:
                d["last_watched"] = newer(d.get("last_watched"), sd.replace(" ", "T"))

    # ---- Finalize each show record --------------------------------------
    out_shows = []
    for sid, d in shows.items():
        d["followed"] = sid in followed_ids
        d["favorited"] = sid in favorite_ids
        cat = d.get("status_category")
        if cat in WATCHED_STATUSES:
            d["watched"] = True
        elif cat in UNWATCHED_STATUSES:
            d["watched"] = False
        elif d.get("watched_episode_count"):
            d["watched"] = d["watched_episode_count"] > 0
        elif d.get("watched_episodes"):
            d["watched"] = True
        else:
            d["watched"] = False
        # The per-episode SxxEyy list is only as complete as the cache: the
        # "seen episodes" endpoint was cached per show for the latest season(s)
        # only, so it is often a subset of watched_episode_count. Flag that so
        # the list is never mistaken for the full watch history.
        if d.get("watched_episodes") and d.get("watched_episode_count") \
                and len(d["watched_episodes"]) < d["watched_episode_count"]:
            d["watched_episodes_partial"] = True
        # Expose the *_date fields as full ISO 8601 timestamps (keep the time
        # component, don't truncate to the date). Suppress epoch/zero placeholders
        # (1970-01-01 / 0001-01-01) that TV Time uses when there is no real date
        # (e.g. a followed-but-never-watched show).
        for f in ("followed_at", "favorited_at", "last_watched"):
            val = d.get(f)
            if val and len(val) >= 10 and val[:4] not in ("1970", "0001"):
                d[f + "_date"] = val.replace(" ", "T")
        out_shows.append(d)

    # Stable, human-friendly ordering: by name.
    out_shows.sort(key=lambda x: (x.get("name") or "").lower())

    # Reorder keys per show for readable output.
    key_order = ["id", "name", "followed", "favorited", "watched", "status_category",
                 "show_status", "network", "country",
                 "followed_at_date", "last_watched_date",
                 "watched_episode_count", "aired_episode_count",
                 "is_up_to_date", "is_archived", "is_for_later",
                 "last_watched_episode", "watched_episodes", "watched_episodes_partial",
                 "hashtag", "poster", "favorited_at_date"]
    # Guarantee the JSON documents every field it can emit (and no phantom fields).
    assert set(key_order) == set(SHOW_FIELD_DOCS), \
        "SHOW_FIELD_DOCS must document exactly the fields in key_order"
    clean_shows = []
    for d in out_shows:
        clean_shows.append({k: d[k] for k in key_order if k in d and d[k] not in (None, "")})

    status_breakdown = defaultdict(int)
    for d in out_shows:
        if d.get("status_category"):
            status_breakdown[d["status_category"]] += 1

    result = {
        "source": "TV Time DioCache.db (offline cache recovery)",
        "notes": {
            "general": [
                "Every show listed is a followed show (the follow list is the superset).",
                "A field is omitted from a show entry when the cache held no value for it.",
                "'watched' and 'status_category' are complete for all followed shows, taken from "
                "TV Time's own per-show status.",
                "'watched_episode_count' / 'aired_episode_count' were only cached for some shows "
                "(favorites and recently-opened shows); where present they are the authoritative totals.",
                "'watched_episodes' (SxxEyy) could only be recovered for shows whose episode list was "
                "cached, and usually covers only the most recent season(s) — see 'watched_episodes_partial'. "
                "'last_watched_episode' is the furthest-watched episode for those shows.",
                "No favorite or watched movies were present in the cache (the favorite-movies list was empty).",
            ],
            "fields": SHOW_FIELD_DOCS,
        },
        "user": user,
        "summary": {
            "shows_total": len(clean_shows),
            "followed": sum(1 for d in out_shows if d["followed"]),
            "favorited": sum(1 for d in out_shows if d["favorited"]),
            "watched": sum(1 for d in out_shows if d["watched"]),
            "with_episode_counts": sum(1 for d in out_shows if d.get("watched_episode_count")),
            "with_watched_episode_detail": sum(1 for d in out_shows if d.get("watched_episodes")),
            "status_breakdown": dict(status_breakdown),
        },
        "shows": clean_shows,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # ---- CSV: same per-show data, one row per show ----------------------
    # watched_episodes becomes a single comma-separated column ("S01E01,S01E02,..").
    # csv quotes that field automatically so it stays one column.
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(key_order)
        for d in clean_shows:
            w.writerow([_csv_value(d.get(k)) for k in key_order])

    s = result["summary"]
    print("Wrote %s" % out_path)
    print("Wrote %s" % csv_path)
    print("  shows: %d  (followed=%d, favorited=%d, watched=%d)"
          % (s["shows_total"], s["followed"], s["favorited"], s["watched"]))
    print("  with episode counts: %d   with per-episode detail: %d"
          % (s["with_episode_counts"], s["with_watched_episode_detail"]))
    print("  status: %s" % s["status_breakdown"])


def _csv_value(v):
    """Render a JSON value for a CSV cell: lists -> comma-joined, bools lowercased."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return ",".join(str(x) for x in v)
    return v


def merge_counts(d, watched, aired, up_to_date, archived, for_later):
    """Merge watch counts from several snapshots, keeping the most-progressed."""
    if watched is not None:
        d["watched_episode_count"] = max(d.get("watched_episode_count", 0), watched)
    if aired is not None:
        d["aired_episode_count"] = max(d.get("aired_episode_count", 0), aired)
    for field, val in (("is_up_to_date", up_to_date),
                       ("is_archived", archived),
                       ("is_for_later", for_later)):
        if val is not None:
            d[field] = val


if __name__ == "__main__":
    main()