#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
presentation_generator.py - 簡報生成器主程式
"""

import json
from pathlib import Path
from typing import Optional
from jinja2 import Template

from slide_model import Presentation, Slide, SlideTheme
from html_renderer import HTMLRenderer


class PresentationGenerator:
    """簡報生成器"""
    
    def __init__(self, presentation: Optional[Presentation] = None):
        self.presentation = presentation or Presentation()
    
    def load_from_json(self, filepath: str) -> None:
        """從 JSON 檔案載入專案"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.presentation = Presentation.from_dict(data)
    
    def save_to_json(self, filepath: str) -> None:
        """儲存專案為 JSON 檔案"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.presentation.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_from_markdown(self, filepath: str) -> None:
        """從 Markdown 檔案載入投影片"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析 Markdown 檔案
        slides = self._parse_markdown_file(content)
        self.presentation.slides = slides
    
    def _parse_markdown_file(self, content: str) -> list[Slide]:
        """解析 Markdown 檔案內容"""
        slides = []
        
        # 分割投影片（以 --- 或 # 開頭的標題為分隔）
        parts = content.split('\n---\n')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            lines = part.split('\n')
            title = ""
            subtitle = ""
            content_lines = []
            
            # 解析標題和內容
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 主標題 (# 開頭)
                if line.startswith('# '):
                    title = line[2:].strip()
                    i += 1
                    continue
                
                # 副標題 (## 開頭)
                if line.startswith('## '):
                    subtitle = line[3:].strip()
                    i += 1
                    continue
                
                # 其他內容
                content_lines.append(lines[i])
                i += 1
            
            slide = Slide(
                title=title,
                subtitle=subtitle,
                content='\n'.join(content_lines).strip()
            )
            slides.append(slide)
        
        return slides
    
    def generate_html(self, output_path: str, template_path: Optional[str] = None) -> None:
        """生成 HTML 簡報"""
        # 使用預設模板或自訂模板
        if template_path is None:
            template_path = Path(__file__).parent / 'template.html'
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        template = Template(template_content)
        
        # 渲染每張投影片
        renderer = HTMLRenderer(self.presentation.theme)
        slide_htmls = []
        
        for i, slide in enumerate(self.presentation.slides):
            slide_html = renderer.render_slide(slide, i)
            slide_htmls.append(slide_html)
        
        # 組合最終 HTML
        html = template.render(
            title=self.presentation.title,
            theme=self.presentation.theme.to_dict(),
            slides=slide_htmls,
        )
        
        # 寫入檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def generate_individual_slides(self, output_dir: str) -> None:
        """生成個別的投影片 HTML 檔案"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        renderer = HTMLRenderer(self.presentation.theme)
        
        for i, slide in enumerate(self.presentation.slides):
            slide_html = renderer.render_slide(slide, i)
            
            # 儲存個別投影片
            slide_file = output_path / f'slide_{i:03d}.html'
            with open(slide_file, 'w', encoding='utf-8') as f:
                f.write(slide_html)
    
    def add_slide(self, title: str = "", subtitle: str = "", content: str = "") -> None:
        """新增投影片"""
        slide = Slide(title=title, subtitle=subtitle, content=content)
        self.presentation.add_slide(slide)
    
    def remove_slide(self, index: int) -> None:
        """移除投影片"""
        self.presentation.remove_slide(index)
    
    def move_slide(self, from_index: int, to_index: int) -> None:
        """移動投影片"""
        self.presentation.move_slide(from_index, to_index)


def main():
    """命令列介面"""
    import argparse
    
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
        print(f"✓ 已建立新專案: {output}")
    
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
        print(f"✓ 已生成簡報: {output}")
    
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
        print(f"✓ 已匯出 {len(gen.presentation.slides)} 張投影片到: {output_dir}")


if __name__ == '__main__':
    main()
