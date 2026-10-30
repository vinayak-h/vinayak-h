#!/usr/bin/env python3
"""One-time local Spotify Authorization Code flow; prints a refresh token."""
import base64, http.server, json, os, secrets, urllib.parse, urllib.request, webbrowser

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPES = "user-read-currently-playing user-read-playback-state"
STATE = secrets.token_urlsafe(20)
RESULT = {}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if parsed.path != "/callback" or params.get("state", [""])[0] != STATE:
            self.send_response(400); self.end_headers(); self.wfile.write(b"Invalid callback state."); return
        RESULT["code"] = params.get("code", [None])[0]
        self.send_response(200 if RESULT["code"] else 400)
        self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(b"<h2>Spotify authorization received.</h2><p>Close this tab and return to the terminal.</p>")
    def log_message(self, *_): pass

def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise SystemExit("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET first.")
    query = urllib.parse.urlencode({"client_id": CLIENT_ID, "response_type": "code",
        "redirect_uri": REDIRECT_URI, "scope": SCOPES, "state": STATE})
    url = "https://accounts.spotify.com/authorize?" + query
    print("Opening Spotify authorization. If it does not open, visit:\\n", url)
    webbrowser.open(url)
    server = http.server.HTTPServer(("127.0.0.1", 8888), Handler)
    server.handle_request(); server.server_close()
    if not RESULT.get("code"): raise SystemExit("Spotify authorization did not return a code.")
    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "authorization_code", "code": RESULT["code"],
                                   "redirect_uri": REDIRECT_URI}).encode()
    req = urllib.request.Request("https://accounts.spotify.com/api/token", data=data,
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=20) as response: tokens = json.load(response)
    print("\\nAdd this as a GitHub Actions repository secret:")
    print("SPOTIFY_REFRESH_TOKEN =", tokens["refresh_token"])
    print("\\nNever commit this token or share it publicly.")

if __name__ == "__main__": main()
