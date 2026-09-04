#!/usr/bin/env python3
"""One-time Spotify authorisation, and a read of your top tracks.

    python spotify_top.py auth     # opens a browser once, prints a refresh token
    python spotify_top.py top      # prints your current top tracks

Credentials come from .env in this directory (gitignored), or from real
environment variables, which take precedence. Nothing is written to disk by
this script: the point is to see what the API returns before wiring it into a
build.

Set up at https://developer.spotify.com/dashboard - create an app, and add this
exact redirect URI to it:

    http://127.0.0.1:8888/callback

Spotify no longer accepts `localhost` as a redirect host, only the loopback IP.
The only scope needed is user-top-read.
"""

from __future__ import annotations

import base64
import http.server
import json
import os
import pathlib
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

def load_env(path: str = ".env") -> None:
    """Read KEY=VALUE lines into the environment. Real values already set in
    the environment win, so a shell export can override the file."""
    f = pathlib.Path(__file__).parent / path
    if not f.exists():
        return
    for line in f.read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env()

# Windows consoles default to cp1252, which cannot encode plenty of ordinary
# track titles (curly quotes, accents, dashes).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "user-top-read"


def basic_auth() -> str:
    raw = f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def post_token(fields: dict) -> dict:
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=urllib.parse.urlencode(fields).encode(),
        headers={
            "Authorization": basic_auth(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=20).read())
    except urllib.error.HTTPError as exc:
        sys.exit(f"token request failed ({exc.code}): {exc.read().decode()}")


def need_app_creds() -> None:
    if not CLIENT_ID or not CLIENT_SECRET:
        sys.exit(
            "SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET are empty.\n"
            "Fill them in in .env (see the comments at the top of that file)."
        )


def auth() -> None:
    """Authorisation Code flow. Run once; the refresh token does not expire."""
    need_app_creds()
    state = secrets.token_urlsafe(16)
    query = urllib.parse.urlencode(
        {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPE,
            "state": state,
        }
    )
    url = f"https://accounts.spotify.com/authorize?{query}"
    captured: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            captured.update(
                {k: v[0] for k, v in
                 urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()}
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            ok = "code" in captured and captured.get("state") == state
            self.wfile.write(
                b"<h2>Done - you can close this tab.</h2>" if ok
                else b"<h2>Authorisation failed. Check the terminal.</h2>"
            )

        def log_message(self, *args):  # keep the console quiet
            pass

    print("Opening your browser to authorise...")
    print(f"If it does not open, visit:\n  {url}\n")
    webbrowser.open(url)

    with http.server.HTTPServer(("127.0.0.1", 8888), Handler) as httpd:
        httpd.handle_request()

    if captured.get("state") != state:
        sys.exit("state mismatch - aborted")
    if "code" not in captured:
        sys.exit(f"no code returned: {captured}")

    tok = post_token(
        {
            "grant_type": "authorization_code",
            "code": captured["code"],
            "redirect_uri": REDIRECT_URI,
        }
    )
    print("\nSPOTIFY_REFRESH_TOKEN:\n")
    print(f"  {tok['refresh_token']}\n")
    print("Paste it into .env as SPOTIFY_REFRESH_TOKEN, then run:")
    print("    python spotify_top.py top\n")
    print("Treat it like a password: it grants read access to your listening")
    print("history until you revoke the app at spotify.com/account/apps.")


def access_token() -> str:
    need_app_creds()
    refresh = os.environ.get("SPOTIFY_REFRESH_TOKEN", "")
    if not refresh:
        sys.exit("SPOTIFY_REFRESH_TOKEN is empty in .env - "
                 "run `python spotify_top.py auth` to get one")
    return post_token({"grant_type": "refresh_token", "refresh_token": refresh})[
        "access_token"
    ]


def fetch_top(time_range: str, limit: int = 50) -> list[dict]:
    """Ranked by play count. 50 is the API maximum."""
    token = access_token()
    query = urllib.parse.urlencode({"time_range": time_range, "limit": limit})
    req = urllib.request.Request(
        f"https://api.spotify.com/v1/me/top/tracks?{query}",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=20).read()).get("items", [])
    except urllib.error.HTTPError as exc:
        sys.exit(f"top/tracks failed ({exc.code}): {exc.read().decode()}")


def cap_per_album(tracks: list[dict], cap: int) -> list[dict]:
    """Keep at most `cap` tracks per album, preserving rank order.

    Ranking by play count means an album on repeat crowds out everything else;
    this thins each album to its own highest-ranked tracks.
    """
    seen: dict[str, int] = {}
    kept = []
    for t in tracks:
        album = t["album"]["id"]
        if seen.get(album, 0) >= cap:
            continue
        seen[album] = seen.get(album, 0) + 1
        kept.append(t)
    return kept


def top(time_range: str = "short_term", show: int = 10, per_album: int = 0) -> None:
    tracks = fetch_top(time_range)
    total = len(tracks)
    if per_album:
        tracks = cap_per_album(tracks, per_album)

    note = f", capped at {per_album}/album from {total} ranked" if per_album else ""
    print(f"\n{time_range}{note}\n")
    for i, t in enumerate(tracks[:show], 1):
        artists = ", ".join(a["name"] for a in t["artists"])
        ms = t["duration_ms"]
        print(f"{i:2}. {t['name'][:40]:42} {artists[:22]:24} "
              f"{t['album']['name'][:24]:26} {ms // 60000}:{ms // 1000 % 60:02d}  {t['id']}")
    print()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth", help="one-time browser authorisation")
    t = sub.add_parser("top", help="print top tracks")
    t.add_argument("range", nargs="?", default="short_term",
                   choices=["short_term", "medium_term", "long_term"],
                   help="short_term ~4 weeks, medium_term ~6 months, long_term ~years")
    t.add_argument("--per-album", type=int, default=0, metavar="N",
                   help="keep at most N tracks from any one album")
    t.add_argument("--show", type=int, default=10, metavar="N",
                   help="how many to print (default 10)")

    args = ap.parse_args()
    if args.cmd == "auth":
        auth()
    else:
        top(args.range, show=args.show, per_album=args.per_album)
