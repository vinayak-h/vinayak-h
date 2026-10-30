#!/usr/bin/env python3
"""Refresh Spotify playback and render a safe, minimal now-playing SVG."""
import base64, json, os, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path("assets/spotify.svg")

def card(title, subtitle, note=""):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="112" viewBox="0 0 1000 112">
<rect width="100%" height="100%" rx="12" fill="#0B0B0C" stroke="#303036"/>
<circle cx="52" cy="56" r="20" fill="#202124"/>
<path d="M42 49c12-4 23-1 29 4M44 56c9-3 18-1 24 3M46 63c7-2 13-1 19 2" fill="none" stroke="#A1A1AA" stroke-width="2" stroke-linecap="round"/>
<text x="88" y="48" fill="#F4F4F5" font-size="17" font-weight="600" font-family="Inter,Segoe UI,Arial">{escape(title)}</text>
<text x="88" y="73" fill="#A1A1AA" font-size="13" font-family="Inter,Segoe UI,Arial">{escape(subtitle)}</text>
<text x="972" y="95" text-anchor="end" fill="#71717A" font-size="10" font-family="Inter,Segoe UI,Arial">{escape(note)}</text>
</svg>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")

def post_token(client_id, client_secret, refresh_token):
    body = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": refresh_token}).encode()
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request("https://accounts.spotify.com/api/token", data=body,
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)["access_token"]

def main():
    cid, secret, refresh = (os.getenv(k) for k in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN"))
    if not all((cid, secret, refresh)):
        card("Spotify integration not configured", "Add the three Spotify repository secrets to enable this panel.", "OPTIONAL")
        return
    access = post_token(cid, secret, refresh)
    req = urllib.request.Request("https://api.spotify.com/v1/me/player/currently-playing",
                                 headers={"Authorization": f"Bearer {access}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read()
            payload = json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 404):
            card("Spotify playback unavailable", "No active playback or no currently-playing item.", "NOT PLAYING")
            return
        raise
    if not payload or not payload.get("is_playing") or not payload.get("item"):
        card("Not listening to Spotify right now", "When playback starts, the current track will appear here.", "NOT PLAYING")
        return
    item = payload["item"]
    artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
    album = item.get("album", {}).get("name", "")
    subtitle = f"{artists} · {album}" if album else artists
    card(item.get("name", "Unknown track"), subtitle, "NOW PLAYING · " + datetime.now(timezone.utc).strftime("%H:%M UTC"))

if __name__ == "__main__":
    main()
