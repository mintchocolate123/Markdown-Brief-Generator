#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli.py - 命令列介面
"""

import argparse
import sys
from typing import List, Optional

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
    parser.add_argument('command', choices=['build'], help='指令：build (生成)')
    parser.add_argument('-i', '--input', help='輸入的 Markdown 檔案')
    parser.add_argument('-o', '--output', help='輸出檔案')
    parser.add_argument('-t', '--title', help='簡報標題（未指定時使用第一張投影片的標題或檔名）')
    parser.add_argument('--template', help='自訂模板路徑')
    
    args = parser.parse_args(argv)
    
    gen = PresentationGenerator()
    
    if args.command == 'build':
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
