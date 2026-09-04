#!/usr/bin/env python3
"""Refresh the track list shown under "music".

    python refresh_music.py              # metadata for the ids in content.yaml
    python refresh_music.py --from-top   # pull my current Spotify top tracks

Writes music.yaml and hanyuc.com/data/images/music/*.jpg, both committed, so
that build.py never touches the network and a Spotify outage cannot break a
build or a deploy.

Titles, artists and album art need no credentials: oEmbed is public, and the
artist name comes from the public embed page. If Spotify changes the shape of
that page the artist is omitted rather than the run failing.

--from-top additionally reads /v1/me/top/tracks, which is user-scoped and needs
SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET and SPOTIFY_REFRESH_TOKEN - from .env
locally, or from repo secrets in CI. Run `python spotify_top.py auth` once to
get a refresh token.

Ranking is Spotify's own affinity score: undocumented, and dominated by repeat
plays. Without --per-album a single album on repeat fills the whole list. No
Spotify endpoint exposes listening duration.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).parent
ART_DIR = ROOT / "hanyuc.com" / "data" / "images" / "music"
ART_REL = "data/images/music"
CACHE = ROOT / "music.yaml"
ART_PX = 128  # displayed at 40px; 128 covers 2x screens

UA = {"User-Agent": "Mozilla/5.0 (compatible; hanyuc.com build script)"}

# Windows consoles default to cp1252, which cannot encode plenty of ordinary
# track titles. Only affects what is printed; the YAML is written as UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_env(path: str = ".env") -> None:
    """Read KEY=VALUE lines into the environment; real env vars win."""
    f = ROOT / path
    if not f.exists():
        return
    for line in f.read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env()


def fetch(url: str, headers: dict | None = None, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout).read()


# --- public endpoints, no credentials ---------------------------------------

def oembed(track_id: str) -> dict:
    target = urllib.parse.quote(f"https://open.spotify.com/track/{track_id}", safe="")
    return json.loads(fetch(f"https://open.spotify.com/oembed?url={target}"))


def artist_and_duration(track_id: str) -> tuple[str, str]:
    """Scraped from the embed page. Degrades to ('', '')."""
    try:
        html = fetch(f"https://open.spotify.com/embed/track/{track_id}").decode(
            "utf-8", "replace"
        )
        blob = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html,
            re.S,
        )
        entity = json.loads(blob.group(1))["props"]["pageProps"]["state"]["data"][
            "entity"
        ]
        artists = ", ".join(a["name"] for a in entity.get("artists", []))
        ms = entity.get("duration") or 0
        return artists, (f"{ms // 60000}:{ms // 1000 % 60:02d}" if ms else "")
    except Exception as exc:  # noqa: BLE001 - any shape change is non-fatal
        print(f"    artist lookup failed ({exc.__class__.__name__}); continuing")
        return "", ""


def save_art(track_id: str, url: str) -> str:
    """Download and downscale, so the page serves no third-party images."""
    from PIL import Image

    ART_DIR.mkdir(parents=True, exist_ok=True)
    im = Image.open(io.BytesIO(fetch(url))).convert("RGB")
    im.thumbnail((ART_PX, ART_PX), Image.LANCZOS)
    out = ART_DIR / f"{track_id}.jpg"
    im.save(out, "JPEG", quality=82, optimize=True)
    return f"{ART_REL}/{track_id}.jpg"


# --- user-scoped endpoint, needs OAuth --------------------------------------

def access_token() -> str:
    cid = os.environ.get("SPOTIFY_CLIENT_ID", "")
    secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    refresh = os.environ.get("SPOTIFY_REFRESH_TOKEN", "")
    if not (cid and secret and refresh):
        sys.exit(
            "--from-top needs SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET and "
            "SPOTIFY_REFRESH_TOKEN (in .env locally, or repo secrets in CI)."
        )
    auth = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=urllib.parse.urlencode(
            {"grant_type": "refresh_token", "refresh_token": refresh}
        ).encode(),
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=20).read())["access_token"]
    except urllib.error.HTTPError as exc:
        sys.exit(f"token refresh failed ({exc.code}): {exc.read().decode()}")


def cap_per_album(tracks: list[dict], cap: int) -> list[dict]:
    """Keep at most `cap` tracks per album, preserving rank order."""
    seen: dict[str, int] = {}
    kept = []
    for t in tracks:
        album = t["album"]["id"]
        if seen.get(album, 0) >= cap:
            continue
        seen[album] = seen.get(album, 0) + 1
        kept.append(t)
    return kept


def top_ids(time_range: str, count: int, per_album: int) -> list[str]:
    query = urllib.parse.urlencode({"time_range": time_range, "limit": 50})
    try:
        data = json.loads(
            fetch(
                f"https://api.spotify.com/v1/me/top/tracks?{query}",
                headers={"Authorization": f"Bearer {access_token()}"},
            )
        )
    except urllib.error.HTTPError as exc:
        sys.exit(f"top/tracks failed ({exc.code}): {exc.read().decode()}")

    tracks = data.get("items", [])
    if per_album:
        tracks = cap_per_album(tracks, per_album)
    return [t["id"] for t in tracks[:count]]


# --- build the cache ---------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--from-top", action="store_true",
                    help="pull my Spotify top tracks instead of using content.yaml")
    ap.add_argument("--time-range", default="short_term",
                    choices=["short_term", "medium_term", "long_term"],
                    help="short_term ~4 weeks (default), medium_term ~6 months")
    ap.add_argument("--count", type=int, default=10, help="how many to keep")
    ap.add_argument("--per-album", type=int, default=2, metavar="N",
                    help="keep at most N tracks from any one album (0 = no cap)")
    args = ap.parse_args()

    if args.from_top:
        ids = top_ids(args.time_range, args.count, args.per_album)
        print(f"top {args.time_range}, max {args.per_album or 'any'} per album "
              f"-> {len(ids)} tracks")
    else:
        content = yaml.safe_load((ROOT / "content.yaml").read_text("utf-8"))
        ids = content.get("music") or []
        if not ids:
            sys.exit("content.yaml has no `music:` ids")

    tracks = []
    for track_id in ids:
        try:
            meta = oembed(track_id)
        except urllib.error.HTTPError as exc:
            sys.exit(f"oEmbed failed for {track_id}: {exc}")
        artist, length = artist_and_duration(track_id)
        tracks.append(
            {
                "id": track_id,
                "title": meta["title"],
                "artist": artist,
                "length": length,
                "art": save_art(track_id, meta["thumbnail_url"]),
            }
        )
        print(f"  {meta['title']} - {artist or '(unknown artist)'} {length}")

    # Drop art for tracks no longer listed, so the directory does not
    # accumulate covers forever as the list rotates.
    keep = {t["id"] for t in tracks}
    if ART_DIR.exists():
        for f in sorted(ART_DIR.glob("*.jpg")):
            if f.stem not in keep:
                f.unlink()
                print(f"  removed stale art {f.name}")

    CACHE.write_text(
        "# Generated by refresh_music.py - do not edit by hand.\n"
        "# build.py reads this so it never needs the network.\n"
        + yaml.safe_dump({"tracks": tracks}, allow_unicode=True, sort_keys=False),
        "utf-8",
    )
    print(f"\nwrote {CACHE} ({len(tracks)} tracks)")


if __name__ == "__main__":
    main()
