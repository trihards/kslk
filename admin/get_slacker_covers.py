#!/usr/bin/env python3
"""
Download the cover art (and descriptions) for every Slacker Chill playlist into slacker_covers.zip.

Uses the same Spotify developer app as get_playlist_ids.py (same Client ID,
same redirect URI: http://127.0.0.1:8888/callback). Nothing to install.

Run:  python3 get_slacker_covers.py      (Windows: py get_slacker_covers.py)
"""
import base64, csv, hashlib, http.server, json, os, secrets, shutil, sys, threading, time
import urllib.parse, urllib.request, urllib.error, webbrowser

REDIRECT = "http://127.0.0.1:8888/callback"
SCOPES = "playlist-read-private playlist-read-collaborative"
FOLDER = "slacker_covers"


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


def pick_image(images):
    """Prefer a ~300px version to keep the zip small; fall back to whatever exists."""
    if not images:
        return None
    sized = [i for i in images if i.get("width")]
    mid = [i for i in sized if 250 <= i["width"] <= 700]
    if mid:
        return min(mid, key=lambda i: i["width"])["url"]
    return images[0]["url"]


def main():
    client_id = (sys.argv[1] if len(sys.argv) > 1 else input("Paste your Spotify app's Client ID: ")).strip()
    verifier = b64url(secrets.token_bytes(64))
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    code = get_code(client_id, challenge, secrets.token_urlsafe(16))
    token = post_form("https://accounts.spotify.com/api/token", {
        "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
        "client_id": client_id, "code_verifier": verifier,
    })["access_token"]

    playlists, url = [], "https://api.spotify.com/v1/me/playlists?limit=50"
    while url:
        page = get_json(url, token)
        for p in page.get("items") or []:
            if p and p.get("name", "").lower().startswith("slacker"):
                playlists.append(p)
        url = page.get("next")
    print(f"Found {len(playlists)} Slacker Chill playlists. Downloading covers...")

    os.makedirs(FOLDER, exist_ok=True)
    rows = []
    for n, p in enumerate(playlists, 1):
        img = pick_image(p.get("images"))
        kind = "none" if not img else ("auto mosaic" if "mosaic.scdn.co" in img else "custom")
        if img:
            try:
                with urllib.request.urlopen(img) as r, open(os.path.join(FOLDER, f"{p['id']}.jpg"), "wb") as f:
                    f.write(r.read())
            except Exception as e:
                kind = f"download failed: {e}"
            time.sleep(0.05)
        rows.append({"name": p.get("name", ""), "id": p["id"], "cover": kind, "description": p.get("description") or ""})
        if n % 25 == 0:
            print(f"  {n} done...")

    with open(os.path.join(FOLDER, "covers.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "id", "cover", "description"])
        w.writeheader()
        w.writerows(rows)
    shutil.make_archive(FOLDER, "zip", FOLDER)
    custom = sum(r["cover"] == "custom" for r in rows)
    print(f"\nDone. {custom} custom covers, {len(rows) - custom} without one. Drop {FOLDER}.zip in the chat.")


if __name__ == "__main__":
    main()
