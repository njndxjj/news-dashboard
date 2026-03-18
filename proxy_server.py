#!/usr/bin/env python3
"""
轻量级反向代理服务器
- 统一入口：http://localhost:8080
- /admin/* → http://localhost:5000/admin/* (管理后台)
- /api/* → http://localhost:5000/api/* (后端 API)
- /* → http://localhost:3000/* (前端用户界面)
"""

import os
import sys

# 添加项目根目录到路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 导入配置
from config import PROXY_PORT, BACKEND_URL, FRONTEND_URL

import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
from functools import partial


class ReverseProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 判断请求路由
        if self.path.startswith('/admin') or self.path.startswith('/api'):
            target_url = BACKEND_URL + self.path
        else:
            target_url = FRONTEND_URL + self.path

        self._proxy_request(target_url)

    def do_POST(self):
        if self.path.startswith('/admin') or self.path.startswith('/api'):
            target_url = BACKEND_URL + self.path
        else:
            target_url = FRONTEND_URL + self.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else None

        self._proxy_request(target_url, post_data=post_data, method='POST')

    def do_PUT(self):
        self._handle_method('PUT')

    def do_DELETE(self):
        self._handle_method('DELETE')

    def _handle_method(self, method):
        if self.path.startswith('/admin') or self.path.startswith('/api'):
            target_url = BACKEND_URL + self.path
        else:
            target_url = FRONTEND_URL + self.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        self._proxy_request(target_url, post_data=body, method=method)

    def _proxy_request(self, url, post_data=None, method='GET'):
        try:
            req = urllib.request.Request(url, data=post_data, method=method)

            # 复制请求头
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'content-length']:
                    req.add_header(header, value)

            # 发送请求
            with urllib.request.urlopen(req, timeout=30) as response:
                # 复制响应头
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() not in ['transfer-encoding', 'connection']:
                        self.send_header(header, value)
                self.end_headers()

                # 复制响应内容
                self.wfile.write(response.read())

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(f'{{"error": "Backend error: {e.reason}"}}'.encode())
        except urllib.error.URLError as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(f'{{"error": "Backend unavailable: {e.reason}"}}'.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(f'{{"error": "Proxy error: {str(e)}"}}'.encode())

    def log_message(self, format, *args):
        # 自定义日志格式
        print(f"[Proxy] {self.address_string()} - {format % args}")


def main():
    handler = ReverseProxyHandler
    httpd = socketserver.TCPServer(("", PROXY_PORT), handler)

    print("=" * 60)
    print("🔄 反向代理服务器已启动")
    print("=" * 60)
    print(f"统一入口：http://localhost:{PROXY_PORT}")
    print(f"")
    print("路由规则:")
    print(f"  /admin/* → {BACKEND_URL}/admin/* (管理后台)")
    print(f"  /api/*   → {BACKEND_URL}/api/* (后端 API)")
    print(f"  /*       → {FRONTEND_URL}/* (前端用户界面)")
    print("=" * 60)
    print("")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Proxy] 正在关闭代理服务器...")
        httpd.shutdown()
        httpd.server_close()
        print("[Proxy] 已关闭")


if __name__ == "__main__":
    main()
