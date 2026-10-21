#!/usr/bin/env python3
"""Local first-run web form. No external API calls and no credential logging."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import time
from urllib.parse import urlsplit
import webbrowser

from configuration_store import ConfigurationError, ConfigurationStore, PACKAGE

ASSETS = PACKAGE / 'assets/configuration-web'
MAX_BODY = 256 * 1024


class ConfigurationServer(HTTPServer):
    def __init__(self, store, port=0):
        self.store = store
        store.status()  # Validate fixed local paths before opening a socket.
        self.token = secrets.token_urlsafe(32)
        self.stopping = False
        self.expires = time.monotonic() + 3600
        super().__init__(('127.0.0.1', port), ConfigurationHandler)
        self.origin = f'http://127.0.0.1:{self.server_port}'
        self.timeout = 1

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5)
        return connection, address

    def handle_error(self, request, client_address):
        pass  # Never include request payloads or exception details in logs.


class ConfigurationHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, value, content_type='application/json; charset=utf-8'):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8') if isinstance(value, dict) else value
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def authorized(self, write=False):
        if self.headers.get('Host') != self.server.origin.removeprefix('http://'):
            self.reply(403, {'error': '本机地址校验失败'})
            return False
        if time.monotonic() > self.server.expires:
            self.reply(403, {'error': '配置会话已过期，请重新启动'})
            return False
        if write and self.headers.get('Origin') != self.server.origin:
            self.reply(403, {'error': '请求来源校验失败'})
            return False
        if write or self.path.startswith('/api/'):
            token = self.headers.get('X-Setup-Token', '')
            if not secrets.compare_digest(token, self.server.token):
                self.reply(403, {'error': '请使用启动命令给出的完整配置链接'})
                return False
        return True

    def do_GET(self):
        if not self.authorized():
            return
        parsed = urlsplit(self.path)
        if parsed.path == '/api/status':
            try:
                result = self.server.store.status()
                self.reply(200, result)
            except (ConfigurationError, OSError):
                self.reply(400, {'error': '无法检查目标目录，请核对符号链接及权限'})
            return
        files = {'/': ('index.html', 'text/html; charset=utf-8'),
                 '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                 '/app.css': ('app.css', 'text/css; charset=utf-8')}
        if parsed.path not in files:
            self.reply(404, {'error': '页面不存在'})
            return
        name, content_type = files[parsed.path]
        self.reply(200, (ASSETS / name).read_bytes(), content_type)

    def do_POST(self):
        if not self.authorized(write=True):
            return
        if self.headers.get('Content-Type') != 'application/json' or self.headers.get('Transfer-Encoding'):
            self.reply(415, {'error': '只接受本机网页发送的 JSON'})
            return
        try:
            length = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            length = -1
        if not 0 < length <= MAX_BODY:
            self.reply(413, {'error': '提交内容过大或长度无效，最大 256 KB'})
            return
        try:
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ConfigurationError('提交格式无效')
            if self.path == '/api/stop':
                self.server.stopping = True
                self.reply(200, {'message': '配置服务已关闭。已保存文件保留，可关闭此页面。'})
                return
            if not self.path.startswith('/api/save/'):
                self.reply(404, {'error': '操作不存在'})
                return
            result = self.server.store.save(self.path.removeprefix('/api/save/'), data)
            self.reply(200, result)
        except ConfigurationError as exc:
            self.reply(400, {'error': str(exc)})
        except (ValueError, OSError, socket.timeout):
            self.reply(400, {'error': '保存失败，请检查文件格式和本机权限；原配置按备份恢复'})
        except Exception:
            self.reply(500, {'error': '本机保存未完成，请检查目录与备份；未输出密钥详情'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--no-browser', action='store_true', help='只打印本机链接，不自动打开浏览器')
    args = parser.parse_args()
    codex_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    try:
        store = ConfigurationStore(args.workspace, codex_home)
        with ConfigurationServer(store) as server:
            url = server.origin + '/#' + server.token
            print('工作区：' + str(store.workspace), flush=True)
            print('本机配置网页：' + url, flush=True)
            print('会话有效期 60 分钟；页面点击关闭或终端 Ctrl+C 停止。保存不代表服务已连接。', flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            while not server.stopping and time.monotonic() < server.expires:
                server.handle_request()
        return 0
    except KeyboardInterrupt:
        return 0
    except (ConfigurationError, OSError):
        print('无法启动，请检查工作区、本机权限和可用端口。')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
