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
    """載入 JSON 或 Markdown，失敗時回傳錯誤訊息"""
    if not path:
        return "請指定輸入檔案 (-i)"
    if path.endswith('.json'):
        gen.load_from_json(path)
    elif path.endswith('.md'):
        gen.load_from_markdown(path)
    else:
        return "不支援的檔案格式（只接受 .md 或 .json）"
    return None


def main(argv: Optional[List[str]] = None) -> int:
    """命令列介面，回傳結束碼"""
    use_utf8_output()
    
    parser = argparse.ArgumentParser(description='HTML 簡報生成器')
    parser.add_argument('command', choices=['new', 'build', 'export-slides'],
                        help='指令：new (新建), build (生成), export-slides (匯出個別投影片)')
    parser.add_argument('-i', '--input', help='輸入檔案 (JSON 或 Markdown)')
    parser.add_argument('-o', '--output', help='輸出檔案或目錄')
    parser.add_argument('-t', '--title', help='簡報標題（未指定時使用檔案自己的標題）')
    parser.add_argument('--template', help='自訂模板路徑')
    
    args = parser.parse_args(argv)
    
    gen = PresentationGenerator()
    
    if args.command == 'new':
        # 建立新專案
        if args.title is not None:
            gen.presentation.title = args.title
        gen.add_slide(title="歡迎", subtitle="這是第一張投影片", content="開始你的簡報內容...")
        
        output = args.output or 'presentation.json'
        gen.save_to_json(output)
        print(f"[OK] 已建立新專案: {output}")
    
    elif args.command == 'build':
        error = _load(gen, args.input)
        if error:
            return _error(error)
        if args.title is not None:
            gen.presentation.title = args.title
        
        # 生成 HTML
        output = args.output or 'presentation.html'
        gen.generate_html(output, args.template)
        print(f"[OK] 已生成簡報: {output}")
    
    elif args.command == 'export-slides':
        error = _load(gen, args.input)
        if error:
            return _error(error)
        
        # 匯出個別投影片
        output_dir = args.output or 'slides'
        gen.generate_individual_slides(output_dir)
        print(f"[OK] 已匯出 {len(gen.presentation.slides)} 張投影片到: {output_dir}")
    
    return 0
