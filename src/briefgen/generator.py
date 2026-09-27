#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generator.py - 簡報生成器
"""

import json
import sys
from pathlib import Path
from typing import Optional
from jinja2 import Template

from briefgen.model import Presentation, Slide, SlideTheme
from briefgen.render.html import HTMLRenderer
from briefgen.parsing.slides import parse_markdown_slides


DEFAULT_TITLE = '簡報'


def markdown_title(slides: list[Slide], filepath: str) -> str:
    """Markdown 簡報的標題：第一張投影片的 # 標題，其次是檔名（不含副檔名），最後是預設值"""
    if slides and slides[0].title:
        return slides[0].title
    return Path(filepath).stem or DEFAULT_TITLE


class PresentationGenerator:
    """簡報生成器"""
    
    def __init__(self, presentation: Optional[Presentation] = None):
        self.presentation = presentation or Presentation()
        self.source_path: Optional[str] = None
    
    def load_from_json(self, filepath: str) -> None:
        """從 JSON 檔案載入專案"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.presentation = Presentation.from_dict(data)
        self.source_path = None
    
    def save_to_json(self, filepath: str) -> None:
        """儲存專案為 JSON 檔案"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.presentation.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_from_markdown(self, filepath: str) -> None:
        """從 Markdown 檔案載入投影片"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析 Markdown 檔案
        slides = parse_markdown_slides(content)
        self.presentation.slides = slides
        self.presentation.title = markdown_title(slides, filepath)
        self.source_path = filepath
    
    def _warn(self, slide_index: int, line_index: int, message: str) -> None:
        """在 stderr 印出格式警告與位置"""
        slide = self.presentation.slides[slide_index]
        if self.source_path and slide.source_lines:
            location = f'{self.source_path}:{slide.source_lines[line_index]}'
        else:
            location = f'投影片 {slide_index + 1} 第 {line_index + 1} 行'
        print(f'{location}: {message}', file=sys.stderr)
    
    def generate_html(self, output_path: str, template_path: Optional[str] = None) -> None:
        """生成 HTML 簡報"""
        # 使用預設模板或自訂模板
        if template_path is None:
            template_path = Path(__file__).parent / 'templates' / 'template.html'
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        template = Template(template_content)
        
        # 渲染每張投影片
        renderer = HTMLRenderer(self.presentation.theme, warn=self._warn)
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
        
        renderer = HTMLRenderer(self.presentation.theme, warn=self._warn)
        
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
