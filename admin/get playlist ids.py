#!/usr/bin/env python3
"""
Dump every playlist in your Spotify library (name + ID + link) to playlist_ids.csv.

Needs: Python 3, nothing to install. A Spotify developer app with this redirect URI:
    http://127.0.0.1:8888/callback

Run:  python get_playlist_ids.py
"""
import base64, csv, hashlib, http.server, json, secrets, sys, threading, time
import urllib.parse, urllib.request, urllib.error, webbrowser

REDIRECT = "http://127.0.0.1:8888/callback"
SCOPES = "playlist-read-private playlist-read-collaborative"
OUT = "playlist_ids.csv"


def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def get_code(client_id, challenge, state):
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state:
                result["code"] = q.get("code", [None])[0]
                result["error"] = q.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "Got it. You can close this tab and go back to the terminal." if result.get("code") \
                else "Spotify didn't hand over a code. Check the terminal."
            self.wfile.write(f"<p style='font:18px sans-serif'>{msg}</p>".encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 8888), Handler)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id": client_id, "response_type": "code", "redirect_uri": REDIRECT,
        "code_challenge_method": "S256", "code_challenge": challenge,
        "scope": SCOPES, "state": state,
    })
    print("\nOpening Spotify login in your browser. If nothing opens, paste this URL:\n" + url + "\n")
    webbrowser.open(url)
    for _ in range(300):
        if result:
            break
        time.sleep(1)
    srv.server_close()
    if not result.get("code"):
        sys.exit(f"No login code received ({result.get('error') or 'timed out'}).")
    return result["code"]


def post_form(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def get_json(url, token):
    while True:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("Retry-After", "5"))
                print(f"  Spotify says slow down, waiting {wait}s...")
                time.sleep(wait)
                continue
            sys.exit(f"Spotify API error {e.code}: {e.read().decode(errors='replace')[:300]}")


def main():
    client_id = (sys.argv[1] if len(sys.argv) > 1 else input("Paste your Spotify app's Client ID: ")).strip()
    verifier = b64url(secrets.token_bytes(64))
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    code = get_code(client_id, challenge, secrets.token_urlsafe(16))

    token = post_form("https://accounts.spotify.com/api/token", {
        "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
        "client_id": client_id, "code_verifier": verifier,
    })["access_token"]

    rows, url = [], "https://api.spotify.com/v1/me/playlists?limit=50"
    while url:
        page = get_json(url, token)
        for p in page.get("items") or []:
            if not p:
                continue
            counts = p.get("tracks") or p.get("items") or {}
            rows.append({
                "name": p.get("name", ""),
                "id": p.get("id", ""),
                "url": f"https://open.spotify.com/playlist/{p.get('id', '')}",
                "owner": (p.get("owner") or {}).get("id", ""),
                "public": p.get("public"),
                "tracks": counts.get("total", "") if isinstance(counts, dict) else "",
            })
        print(f"  {len(rows)} playlists so far...")
        url = page.get("next")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "id", "url", "owner", "public", "tracks"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nDone. Wrote {len(rows)} playlists to {OUT}. Drop that file in the chat.")


if __name__ == "__main__":
    main()
