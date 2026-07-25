# Recovering TV Time data from browser storage (Plan B) — dead end

*[Leia em português](README.md)*

**TL;DR:** We tried to recover TV Time watch history from what the browser had persisted locally (Cache Storage, IndexedDB, Local Storage). We found a real, valid session token and the full account profile in Local Storage — more than expected. Still a dead end: both known API hosts (`api2.tozelabs.com` and `api.tvtime.com`) are dead, each in a different way, and neither answers data requests, token or no token.

Goal: instead of the phone, try to recover watch history from what the **browser** persisted locally for the web app (`https://app.tvtime.com/`) — Cache Storage, IndexedDB and Local Storage — since a DevTools screenshot showed ~20.5MB of stored data even though the watchlist appeared empty with "a network error occurred".

Tested on Brave (Chromium). Result: **real account data was sitting in local storage, and it's still useless** — the backend isn't up to accept it, even with a valid, unexpired session.

## 1. Finding per-origin storage without opening DevTools

Each type of Chromium storage lives in its own place in the profile, and not all of it is indexed by site name in an obvious way:

- **IndexedDB** — one folder per origin, easy to find:

  ```bash
  find ~/.config/BraveSoftware/Brave-Browser -iname "*tvtime*"
  # .../Default/IndexedDB/https_app.tvtime.com_0.indexeddb.leveldb
  ```

- **Cache Storage** (used by service workers) — hash-named folders with no obvious link to the origin. The real origin is in plain text inside each folder's `index.txt`:

  ```bash
  CS=~/.config/BraveSoftware/Brave-Browser/Default/"Service Worker"/CacheStorage
  grep -a -rl "tvtime" "$CS"/*/index.txt
  ```

- **Local Storage** — **a single leveldb shared by every origin in the whole profile**, not one folder per site. A plain-text search here can easily misattribute a value to the wrong site (it happened in this project: a JWT belonging to a completely unrelated service got mistaken for a TV Time token just because it sat nearby in the file). Correct per-key attribution needs a real leveldb parser (e.g. Python's `plyvel`), not `strings`/`grep`.

## 2. What was actually in there, by type

- **Cache Storage**: only `flutter-app-manifest` and `flutter-app-cache` — the web app is a Flutter PWA, and this is just the "app shell" (static JS/assets for offline use), not account data.
- **IndexedDB**: mostly Firebase Remote Config cache (feature flags like `age_gating`, `auth_providers`) and tokens — but decoding the JWTs properly (base64-decoding the payload, not guessing from text proximity) shows they're **Firebase's own internal tokens** (Installations / Google Auth), used only for telemetry/config, not a TV Time API session token.
- **Local Storage**: nothing reliably attributable to TV Time on the first pass (see the shared-leveldb warning above) — **but that changed** once the app managed to authenticate on a later visit (see section 3).

### Warning: reading the on-disk leveldb while the browser is open can lie to you

On the first attempt, reading the leveldb files directly turned up no `flutter.jwtToken` / `flutter.isLoggedIn` key at all. Shortly after, with DevTools open live in the same session, those keys were plainly visible in the **Application → Local Storage** panel. The cause: Chromium keeps recent writes buffered in memory before flushing them to disk, so reading the files from outside while the browser is running can catch a stale state. **If the browser is open, trust DevTools, not an external file read.** To capture the current state reliably without racing that buffer, use the DevTools console itself:

```js
copy(JSON.stringify(Object.fromEntries(Object.entries(localStorage)), null, 2))
```

This runs entirely in the browser, sends nothing anywhere, and gives you the exact `localStorage` at that moment to paste into a file.

## 3. What showed up after a successful login

Once the app managed to authenticate (`flutter.isLoggedIn: "true"`), `localStorage` held, among other `flutter.`-prefixed keys:

- `flutter.jwtToken` / `flutter.jwtRefreshToken` — real session tokens, signed by TV Time itself (`iss`/`aud`: `http://www.tvtime.com`), not generic third-party tokens.
- `flutter.user` — a JSON blob with the full account profile: name, email, timezone, account creation date, and counters like `followed_show_count`, `for_later_show_count`, `stats.time_spent`, `stats.nb_likes`.
- Several `flutter.*_last_action_time` — last-activity timestamps per category (series, movies, comments, etc.).
- `flutter.seriesToSkipWatchPreviousEpisodes` — a list of show IDs.

This overturns the earlier conclusion: the web app **does** persist a useful account summary locally once authenticated — it just doesn't keep the full episode-by-episode history the way the native app's `DioCache.db` does.

## 4. Finding the real API host (from the cached app bundle)

Worth confirming whether the backend is still alive, token or no token. The API host isn't anywhere obvious — but it shows up in plain text inside the very JS/wasm files the service worker cached:

```bash
CS=~/.config/BraveSoftware/Brave-Browser/Default/"Service Worker"/CacheStorage/<hash-from-step-1>/<cache-subfolder>
strings -n 8 "$CS"/*_0 | grep -oE "https?://[a-zA-Z0-9._-]*tozelabs[a-zA-Z0-9._/-]*"
# -> https://api2.tozelabs.com/v2
```

## 5. Testing whether the backend still responds

```bash
curl -v --max-time 10 https://api2.tozelabs.com/v2
```

Result: DNS resolves fine, but the connection on port 443 fails ("no route to host") — the API server is genuinely down, not just returning an auth error. By contrast, the static frontend still responds:

```bash
curl -o /dev/null -w "%{http_code}\n" https://app.tvtime.com/
# -> 200
```

This explains the "network error" in the screenshot: the page (a static frontend, likely still served by a CDN) loads fine, but there's no server on the other end to answer data requests.

## 6. Even with a valid token, the other host is dead too

The JWT (section 3) has `iss`/`aud` pointing at `www.tvtime.com`, a different host from `api2.tozelabs.com`. Worth testing that one too before giving up — and it does respond, unlike the other:

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 8 https://api.tvtime.com/v2/user/me
# -> HTTP 404
```

A 404 could just mean the wrong endpoint. But the response headers tell a different story:

```bash
curl -s -D - --max-time 8 https://api.tvtime.com/v2/user/me
# HTTP/2 404
# server: awselb/2.0
# content-length: 0
```

`server: awselb/2.0` is an AWS Elastic Load Balancer answering on its own, with an empty body — a sign that the load balancer itself still exists (DNS points at it, the infrastructure wasn't fully torn down), but **there's no application server registered behind it** to actually handle the request, whatever the endpoint or token. Trying several paths (`/v2/user/{id}`, `/follows`, `/followed-shows`, etc.) with a real, still-valid `Authorization: Bearer <jwtToken>` gave the same empty 404 every time — not an auth problem, a total absence of application behind the load balancer.

## Conclusion

A real, valid session token turned up, along with the full account profile cached locally — more than expected halfway through this investigation. But it's not enough: both known API hosts (`api2.tozelabs.com` and `api.tvtime.com`) are dead, each in a different way (one refuses the connection outright, the other answers empty from a load balancer with nothing behind it). There's no way to recover account data through the browser, no matter how valid the token is.

If you're chasing something similar for your own recovery project: always confirm the *backend* (not just the frontend, and not just "DNS resolves") still answers with a real application server behind it — an empty 404 from an AWS load balancer is not the same as a 404 from a working API, and neither means a token is worth pursuing.
