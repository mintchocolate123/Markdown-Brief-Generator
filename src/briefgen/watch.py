#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
watch.py - 即時預覽：存檔後重新生成，瀏覽器自動重新載入

只用標準函式庫：輪詢檔案修改時間 + http.server。
live reload 的程式碼只插在伺服器回應的頁面裡，寫到磁碟的 HTML 不含這段程式碼。
"""

import json
import sys
import threading
import time
import webbrowser
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import List, Optional

from briefgen.generator import PresentationGenerator

STATUS_PATH = '/__briefgen/status'
POLL_SECONDS = 0.5

# 每秒詢問伺服器狀態：版本變了就重新載入（網址 hash 保留頁數），否則在角落顯示錯誤與警告
LIVE_RELOAD_SCRIPT = '''
<style>@media print { #briefgen-watch-status { display: none !important; } }</style>
<script>
(function () {
    const loadedVersion = %(version)d;
    const box = document.createElement('div');
    box.id = 'briefgen-watch-status';
    box.style.cssText = 'display:none;position:fixed;top:12px;right:12px;z-index:3000;max-width:45vw;'
        + 'max-height:40vh;overflow:auto;padding:10px 14px;border-radius:8px;font:13px/1.5 monospace;'
        + 'white-space:pre-wrap;background:rgba(20,20,20,.92);color:#fff;box-shadow:0 4px 16px rgba(0,0,0,.5)';
    document.body.appendChild(box);

    function show(status) {
        const lines = [];
        if (status.error) lines.push('[FAIL] ' + status.error + '\\n（顯示的是上一個成功的版本）');
        (status.warnings || []).forEach(w => lines.push('[警告] ' + w));
        box.textContent = lines.join('\\n');
        box.style.borderLeft = status.error ? '4px solid #ff6b6b' : '4px solid #feca57';
        box.style.display = lines.length ? 'block' : 'none';
    }

    async function poll() {
        try {
            const response = await fetch('%(status_path)s', {cache: 'no-store'});
            const status = await response.json();
            if (status.version !== loadedVersion) {
                location.reload();
                return;
            }
            show(status);
        } catch (error) {
            show({error: '無法連線到 briefgen watch（已結束？）'});
        }
        setTimeout(poll, 1000);
    }
    poll();
})();
</script>
'''

NO_BUILD_PAGE = '''<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="UTF-8"><title>briefgen watch</title></head>
<body style="background:#1a1a2e;color:#fff;font-family:sans-serif;padding:40px">
<p>尚未成功生成，修正錯誤並存檔後會自動更新。</p>
</body></html>'''


class Watcher:
    """監看 Markdown 檔，變更時重新生成並記錄狀態"""

    def __init__(self, source: Path, output: Path, title: Optional[str] = None):
        self.source = source
        self.output = output
        self.title = title
        self.html: Optional[str] = None  # 上一個成功的版本（不含 live reload）
        self.version = 0
        self.error: Optional[str] = None
        self.warnings: List[str] = []
        self._signature = None
        self._lock = threading.Lock()

    def _current_signature(self):
        try:
            stat = self.source.stat()
        except OSError:
            return None
        return (stat.st_mtime_ns, stat.st_size)

    def build(self) -> bool:
        """重新生成；成功時寫出 HTML 並更新版本，失敗時保留上一個版本"""
        gen = PresentationGenerator()
        try:
            gen.load_from_markdown(str(self.source))
            if self.title is not None:
                gen.presentation.title = self.title
            html = gen.render_html()
            self.output.write_text(html, encoding='utf-8')
        except Exception as error:  # 讀檔、編碼、模板等任何錯誤都不中斷 watch
            with self._lock:
                self.error = f'{type(error).__name__}: {error}'
            print(f'[FAIL] 生成失敗：{self.error}', file=sys.stderr, flush=True)
            return False

        with self._lock:
            self.html = html
            self.version += 1
            self.error = None
            self.warnings = list(gen.warnings)
        stamp = datetime.now().strftime('%H:%M:%S')
        print(f'[OK] {stamp} 已生成：{self.output}（警告 {len(gen.warnings)} 則）', flush=True)
        return True

    def check(self) -> bool:
        """檔案有變動（修改時間或大小）時重新生成，回傳是否有變動"""
        signature = self._current_signature()
        if signature == self._signature:
            return False
        self._signature = signature
        self.build()
        return True

    def status(self) -> dict:
        with self._lock:
            return {'version': self.version, 'error': self.error, 'warnings': list(self.warnings)}

    def page(self) -> str:
        """給瀏覽器的頁面：上一個成功的版本加上 live reload"""
        with self._lock:
            html, version = self.html or NO_BUILD_PAGE, self.version
        script = LIVE_RELOAD_SCRIPT % {'version': version, 'status_path': STATUS_PATH}
        if '</body>' in html:
            index = html.rindex('</body>')
            return html[:index] + script + html[index:]
        return html + script


class WatchRequestHandler(SimpleHTTPRequestHandler):
    """/ 提供預覽頁、/__briefgen/status 提供狀態，其他路徑為 Markdown 所在資料夾的檔案"""

    def __init__(self, *args, watcher: Watcher, **kwargs):
        self.watcher = watcher
        super().__init__(*args, **kwargs)

    def do_GET(self):
        path = self.path.split('?', 1)[0].split('#', 1)[0]
        if path in ('/', '/index.html'):
            self._send(self.watcher.page().encode('utf-8'), 'text/html; charset=utf-8')
        elif path == STATUS_PATH:
            self._send(json.dumps(self.watcher.status(), ensure_ascii=False).encode('utf-8'),
                       'application/json; charset=utf-8')
        else:
            super().do_GET()

    def _send(self, body: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, format, *args):
        pass  # 不在終端機印每個請求


def serve(watcher: Watcher, port: int = 0) -> ThreadingHTTPServer:
    handler = partial(WatchRequestHandler, watcher=watcher, directory=str(watcher.source.parent))
    server = ThreadingHTTPServer(('127.0.0.1', port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def run(source: Path, output: Path, *, title: Optional[str] = None,
        port: int = 0, open_browser: bool = True) -> int:
    """執行即時預覽直到 Ctrl+C，回傳結束碼"""
    watcher = Watcher(source, output, title=title)
    server = None
    # 啟動途中（生成、開瀏覽器）按 Ctrl+C 也要正常結束
    try:
        watcher.check()
        server = serve(watcher, port)
        url = f'http://127.0.0.1:{server.server_address[1]}/'
        print(f'預覽網址：{url}', flush=True)
        print('存檔後會自動重新生成；按 Ctrl+C 結束', flush=True)
        if open_browser:
            webbrowser.open(url)
        while True:
            time.sleep(POLL_SECONDS)
            watcher.check()
    except KeyboardInterrupt:
        print('\n[OK] 已結束即時預覽', flush=True)
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
    return 0
