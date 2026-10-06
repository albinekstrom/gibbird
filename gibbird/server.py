"""Small HTTP API served by the camera Pi; the frame Pi polls it."""

from __future__ import annotations

import html
import json
import re
import threading
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .names import Species
from .store import Store

_PHOTO_NAME = re.compile(r"[A-Za-z0-9._-]+\.jpg")


def day_start(days: int, now: datetime | None = None) -> float:
    """Local midnight `days - 1` days ago (days=1 -> today)."""
    now = now or datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (midnight - timedelta(days=max(days, 1) - 1)).timestamp()


def summary(store: Store, region: dict[str, Species], days: int) -> dict:
    since = day_start(days)
    species = []
    for row in store.species_since(since):
        sp = region.get(row["sci"].lower())
        species.append({**row, "en": sp.en if sp else row["sci"], "local": sp.local if sp else ""})
    return {"since": since, "generated": time.time(), "days": days, "species": species}


def make_server(store: Store, region: dict[str, Species], photos_dir: Path, host: str, port: int):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            q = parse_qs(url.query)
            if url.path == "/api/summary":
                try:
                    days = int(q.get("days", ["1"])[0])
                except ValueError:
                    return self.send_error(400, "days must be an integer")
                return self._json(summary(store, region, days))
            if url.path == "/api/recent":
                return self._json({"visits": store.recent(50)})
            if url.path == "/api/health":
                return self._json({"ok": True})
            if url.path.startswith("/photos/"):
                return self._photo(url.path.removeprefix("/photos/"))
            if url.path == "/":
                return self._index()
            self.send_error(404)

        def _json(self, payload):
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _photo(self, name: str):
            path = photos_dir / name
            if not _PHOTO_NAME.fullmatch(name) or not path.is_file():
                return self.send_error(404)
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "max-age=60")
            self.end_headers()
            self.wfile.write(body)

        def _index(self):
            data = summary(store, region, 7)
            cards = "".join(
                f'<figure><img src="/photos/{html.escape(s["photo"])}" loading="lazy">'
                f"<figcaption><b>{html.escape(s['local'] or s['en'])}</b><br>{html.escape(s['en'])}"
                f" · {s['visits']} visits</figcaption></figure>"
                for s in data["species"]
            ) or "<p>No birds yet.</p>"
            body = (
                "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
                "<title>GibBird</title><style>body{font-family:system-ui;margin:16px;background:#111;color:#eee}"
                "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}"
                "img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:6px}figure{margin:0}</style>"
                f"<h1>Birds, last 7 days</h1><main>{cards}</main>"
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer((host, port), Handler)


def serve_in_background(server: ThreadingHTTPServer) -> threading.Thread:
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread
