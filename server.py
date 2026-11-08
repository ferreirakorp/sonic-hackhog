#!/usr/bin/env python3
"""Sonic the HackHog — redirect server with visitor logging and API."""
import json, sqlite3, os, secrets
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB = os.environ.get("DB_PATH", "/opt/redirect/visits.db")
REDIRECT_URL = os.environ.get("REDIRECT_URL", "https://wise.com/")
API_KEY = os.environ.get("API_KEY", "")
PORT = int(os.environ.get("PORT", "8099"))

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, ip TEXT, ua TEXT, lang TEXT, method TEXT,
        path TEXT, query TEXT, headers TEXT
    )""")
    conn.commit()
    conn.close()

class Handler(BaseHTTPRequestHandler):
    def _get_visitor_info(self):
        ip = self.headers.get("CF-Connecting-IP",
             self.headers.get("X-Forwarded-For", self.client_address[0]))
        ua = self.headers.get("User-Agent", "")
        lang = self.headers.get("Accept-Language", "")
        parsed = urlparse(self.path)
        return ip, ua, lang, parsed.path, parsed.query

    def _check_api_key(self):
        if not API_KEY:
            return False
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {API_KEY}"

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/visits":
            if not self._check_api_key():
                self._send_json({"error": "unauthorized"}, 401)
                return
            params = parse_qs(parsed.query)
            since = int(params.get("since", ["0"])[0])
            limit = min(int(params.get("limit", ["50"])[0]), 200)
            conn = sqlite3.connect(DB)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM visits WHERE id > ? ORDER BY id ASC LIMIT ?",
                (since, limit)).fetchall()
            conn.close()
            self._send_json({"visits": [dict(r) for r in rows]})
            return

        if path == "/api/health":
            conn = sqlite3.connect(DB)
            count = conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
            conn.close()
            self._send_json({"status": "ok", "total_visits": count,
                             "ts": datetime.now().isoformat()})
            return

        ip, ua, lang, p, query = self._get_visitor_info()
        ts = datetime.now().isoformat()
        hdrs = dict(self.headers)
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT INTO visits (ts,ip,ua,lang,method,path,query,headers) VALUES (?,?,?,?,?,?,?,?)",
            (ts, ip, ua, lang, self.command, p, query, json.dumps(hdrs)))
        conn.commit()
        conn.close()
        print(json.dumps({"ts": ts, "ip": ip, "ua": ua[:60], "method": self.command, "path": p},
              ensure_ascii=False), flush=True)

        self.send_response(302)
        self.send_header("Location", REDIRECT_URL)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    do_HEAD = do_GET
    do_POST = do_GET

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    if not API_KEY:
        API_KEY = secrets.token_urlsafe(32)
        print(f"[!] No API_KEY set — generated: {API_KEY}", flush=True)
    init_db()
    print(f"Sonic the HackHog server on :{PORT} → {REDIRECT_URL}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
