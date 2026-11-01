#!/usr/bin/env python3
"""Refresh Spotify playback and render a safe, minimal now-playing SVG."""
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path("assets/spotify.svg")
TOKEN_URL = "https://accounts.spotify.com/api/token"
PLAYBACK_URL = "https://api.spotify.com/v1/me/player/currently-playing"


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


def read_error_body(error):
    raw = error.read().decode("utf-8", "replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "http_error", "error_description": raw or error.reason}


def post_token(client_id, client_secret, refresh_token):
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()
    request = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        details = read_error_body(error)
        code = details.get("error", "unknown")
        description = details.get("error_description", "No description provided")
        print(f"Spotify token request failed (HTTP {error.code}): {code}")
        print(f"Spotify error description: {description}")
        if code == "invalid_grant":
            print("Action required: re-authorize the Spotify app and replace SPOTIFY_REFRESH_TOKEN in GitHub repository secrets.")
        elif code == "invalid_client":
            print("Action required: verify SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET belong to the same Spotify app.")
        raise SystemExit(1) from None
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"Could not reach Spotify token endpoint: {error}")
        raise SystemExit(1) from None

    access_token = payload.get("access_token")
    if not access_token:
        print("Spotify token response did not contain an access_token.")
        raise SystemExit(1)
    return access_token


def fetch_currently_playing(access_token):
    request = urllib.request.Request(
        PLAYBACK_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        if error.code in (204, 401, 403, 404):
            return None
        details = read_error_body(error)
        print(f"Spotify playback request failed (HTTP {error.code}): {details.get('error', details)}")
        raise SystemExit(1) from None
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"Could not reach Spotify playback endpoint: {error}")
        raise SystemExit(1) from None


def main():
    client_id, client_secret, refresh_token = (
        os.getenv(name, "").strip()
        for name in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN")
    )
    if not all((client_id, client_secret, refresh_token)):
        missing = [
            name for name, value in (
                ("SPOTIFY_CLIENT_ID", client_id),
                ("SPOTIFY_CLIENT_SECRET", client_secret),
                ("SPOTIFY_REFRESH_TOKEN", refresh_token),
            ) if not value
        ]
        print("Missing GitHub Actions secret(s): " + ", ".join(missing))
        card("Spotify integration not configured", "Configure the three Spotify repository secrets to enable this panel.", "OPTIONAL")
        return

    access_token = post_token(client_id, client_secret, refresh_token)
    payload = fetch_currently_playing(access_token)
    if not payload or not payload.get("is_playing") or not payload.get("item"):
        card("Not listening to Spotify right now", "When playback starts, the current track will appear here.", "NOT PLAYING")
        return

    item = payload["item"]
    artists = ", ".join(artist.get("name", "") for artist in item.get("artists", []))
    album = item.get("album", {}).get("name", "")
    subtitle = f"{artists} · {album}" if album else artists
    card(
        item.get("name", "Unknown track"),
        subtitle,
        "NOW PLAYING · " + datetime.now(timezone.utc).strftime("%H:%M UTC"),
    )


if __name__ == "__main__":
    main()
