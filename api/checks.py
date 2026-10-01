"""Vercel function: runs the tests and returns JSON."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.run_all import run_all
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        out = run_all()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(json.dumps(out).encode())
