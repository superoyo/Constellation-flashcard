#!/usr/bin/env python3
"""Minimal static file server that avoids os.getcwd() (sandbox-safe)."""
import functools
import http.server
import socketserver

DIRECTORY = "/Users/anan/Desktop/Claude Code New/kk"
PORT = 8000

Handler = functools.partial(
    http.server.SimpleHTTPRequestHandler, directory=DIRECTORY
)


class Server(socketserver.TCPServer):
    allow_reuse_address = True


with Server(("127.0.0.1", PORT), Handler) as httpd:
    print(f"Serving {DIRECTORY} at http://127.0.0.1:{PORT}/")
    httpd.serve_forever()
