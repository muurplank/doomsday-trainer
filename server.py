"""Doomsday trainer - klein lokaal servertje.

Serveert index.html en schrijft elke poging direct naar doomsday_log.csv
(en de voortgang naar voortgang.json) in dezelfde map als dit bestand.

Starten: dubbelklik op start.command, of:  python3 server.py
"""
import csv
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "doomsday_log.csv"
STATE = HERE / "voortgang.json"
HEADER = ["Timestamp", "Onderdeel", "Bron", "Vraag", "Antwoord", "Juist antwoord", "Goed", "Tijd (s)"]
PORT = int(next((a for a in sys.argv[1:] if a.isdigit()), 8712))
lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif path == "/state":
            self._send(200, STATE.read_bytes() if STATE.exists() else b"{}")
        else:
            self._send(404)

    def do_POST(self):
        # Alleen verzoeken van de pagina zelf accepteren
        origin = self.headers.get("Origin", "")
        if origin and origin not in (f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}"):
            return self._send(403)
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except (ValueError, TypeError):
            return self._send(400)
        with lock:
            if self.path == "/log" and isinstance(data, list) and len(data) == len(HEADER):
                new = not LOG.exists()
                with LOG.open("a", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    if new:
                        w.writerow(HEADER)
                    w.writerow([str(v) for v in data])
            elif self.path == "/state" and isinstance(data, dict):
                tmp = STATE.with_suffix(".tmp")
                tmp.write_text(json.dumps(data), encoding="utf-8")
                tmp.replace(STATE)
            else:
                return self._send(400)
        self._send(200, b"{}")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    url = f"http://localhost:{PORT}/"
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"Draait al - ik open {url}")
        webbrowser.open(url)
        sys.exit(0)
    print(f"Doomsday trainer draait op {url}")
    print(f"Log: {LOG}")
    print("Laat dit venster open tijdens het oefenen. Stoppen: Ctrl+C of venster sluiten.")
    if "--no-open" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGestopt.")
