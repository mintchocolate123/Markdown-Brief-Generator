#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli.py - 命令列介面
"""

import argparse

from briefgen.console import use_utf8_output
from briefgen.generator import PresentationGenerator


def main():
    """命令列介面"""
    use_utf8_output()
    
    parser = argparse.ArgumentParser(description='HTML 簡報生成器')
    parser.add_argument('command', choices=['new', 'build', 'export-slides'],
                        help='指令：new (新建), build (生成), export-slides (匯出個別投影片)')
    parser.add_argument('-i', '--input', help='輸入檔案 (JSON 或 Markdown)')
    parser.add_argument('-o', '--output', help='輸出檔案或目錄')
    parser.add_argument('-t', '--title', default='簡報', help='簡報標題')
    parser.add_argument('--template', help='自訂模板路徑')
    
    args = parser.parse_args()
    
    gen = PresentationGenerator()
    
    if args.command == 'new':
        # 建立新專案
        gen.presentation.title = args.title
        gen.add_slide(title="歡迎", subtitle="這是第一張投影片", content="開始你的簡報內容...")
        
        output = args.output or 'presentation.json'
        gen.save_to_json(output)
        print(f"[OK] 已建立新專案: {output}")
    
    elif args.command == 'build':
        if not args.input:
            print("錯誤：請指定輸入檔案 (-i)")
            return
        
        # 載入專案
        if args.input.endswith('.json'):
            gen.load_from_json(args.input)
        elif args.input.endswith('.md'):
            gen.load_from_markdown(args.input)
            if args.title:
                gen.presentation.title = args.title
        else:
            print("錯誤：不支援的檔案格式")
            return
        
        # 生成 HTML
        output = args.output or 'presentation.html'
        gen.generate_html(output, args.template)
        print(f"[OK] 已生成簡報: {output}")
    
    elif args.command == 'export-slides':
        if not args.input:
            print("錯誤：請指定輸入檔案 (-i)")
            return
        
        # 載入專案
        if args.input.endswith('.json'):
            gen.load_from_json(args.input)
        elif args.input.endswith('.md'):
            gen.load_from_markdown(args.input)
        else:
            print("錯誤：不支援的檔案格式")
            return
        
        # 匯出個別投影片
        output_dir = args.output or 'slides'
        gen.generate_individual_slides(output_dir)
        print(f"[OK] 已匯出 {len(gen.presentation.slides)} 張投影片到: {output_dir}")
