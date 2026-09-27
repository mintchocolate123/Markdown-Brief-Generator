#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli.py - 命令列介面
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from briefgen import watch
from briefgen.console import use_utf8_output
from briefgen.generator import PresentationGenerator


def _error(message: str) -> int:
    """錯誤訊息印到 stderr，回傳結束碼"""
    print(f"[FAIL] 錯誤：{message}", file=sys.stderr)
    return 1


def _load(gen: PresentationGenerator, path: Optional[str]) -> Optional[str]:
    """載入 Markdown，失敗時回傳錯誤訊息"""
    if not path:
        return "請指定輸入檔案 (-i)"
    if not path.endswith('.md'):
        return "不支援的檔案格式（只接受 .md）"
    gen.load_from_markdown(path)
    return None


def main(argv: Optional[List[str]] = None) -> int:
    """命令列介面，回傳結束碼"""
    use_utf8_output()
    
    parser = argparse.ArgumentParser(description='HTML 簡報生成器')
    commands = parser.add_subparsers(dest='command', required=True, metavar='{build,watch}')
    
    build_parser = commands.add_parser('build', help='生成 HTML 簡報')
    build_parser.add_argument('-i', '--input', help='輸入的 Markdown 檔案')
    build_parser.add_argument('-o', '--output', help='輸出檔案')
    build_parser.add_argument('-t', '--title', help='簡報標題（未指定時使用第一張投影片的標題或檔名）')
    build_parser.add_argument('--template', help='自訂模板路徑')
    
    watch_parser = commands.add_parser('watch', help='即時預覽：存檔後自動重新生成並重新載入瀏覽器')
    watch_parser.add_argument('input', help='Markdown 檔案')
    watch_parser.add_argument('-o', '--output', help='輸出檔案（預設為 Markdown 旁的同名 .html）')
    watch_parser.add_argument('-t', '--title', help='簡報標題')
    watch_parser.add_argument('--template', help='自訂模板路徑')
    watch_parser.add_argument('--port', type=int, default=0, help='伺服器埠號（預設自動選擇）')
    watch_parser.add_argument('--no-open', action='store_true', help='不要自動開啟瀏覽器')
    
    args = parser.parse_args(argv)
    
    if args.command == 'watch':
        return _watch(args)
    
    gen = PresentationGenerator()
    error = _load(gen, args.input)
    if error:
        return _error(error)
    if args.title is not None:
        gen.presentation.title = args.title
    
    # 生成 HTML
    output = args.output or 'presentation.html'
    gen.generate_html(output, args.template)
    print(f"[OK] 已生成簡報: {output}")
    return 0


def _watch(args: argparse.Namespace) -> int:
    source = Path(args.input)
    if source.suffix != '.md':
        return _error("不支援的檔案格式（只接受 .md）")
    if not source.is_file():
        return _error(f"找不到檔案：{source}")
    output = Path(args.output) if args.output else source.with_suffix('.html')
    return watch.run(source.resolve(), output, title=args.title, template=args.template,
                     port=args.port, open_browser=not args.no_open)
