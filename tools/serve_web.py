#!/usr/bin/env python3
"""
Локальний сервер для веб-версії (папка web/): відкрийте http://localhost:8765 у браузері.
Картинки, музика і шрифт беруться прямо з assets/ гри (одне джерело для всіх версій), тож після змін
у грі нічого збирати не треба -- просто оновіть сторінку.

    python tools/serve_web.py [порт]
"""
import functools
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
ICON = os.path.join(ROOT, "android", "app", "src", "main", "res", "mipmap-xxxhdpi", "ic_launcher.png")


class Handler(http.server.SimpleHTTPRequestHandler):
    # -- keep-alive: браузер вантажить ~220 картинок кількома з'єднаннями, а не відкриває нове на кожну
    # -- (на Windows кожне нове з'єднання з localhost спершу пробує IPv6 і втрачає ~0.3 сек)
    protocol_version = "HTTP/1.1"
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript"}

    def translate_path(self, path):
        path = path.split("?", 1)[0].split("#", 1)[0]
        if path == "/icon.png":
            return ICON
        if path.startswith("/assets/"):
            return os.path.join(ROOT, *[p for p in path.split("/") if p not in ("", "..")])
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")     # -- після правок -- одразу нова версія
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=WEB))
    print(f"веб-версія: http://localhost:{port}")
    server.serve_forever()
