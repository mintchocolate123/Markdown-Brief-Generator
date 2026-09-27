#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generator.py - 簡報生成器
"""

import sys
from pathlib import Path
from typing import List, Optional
from jinja2 import Template

from briefgen.model import Presentation, Slide
from briefgen.render.html import HTMLRenderer
from briefgen.parsing.slides import parse_markdown_slides


DEFAULT_TITLE = '簡報'


def markdown_title(slides: list[Slide], filepath: str) -> str:
    """Markdown 簡報的標題：第一張投影片的 # 標題、## 副標題，其次是檔名（不含副檔名），最後是預設值"""
    if slides and (slides[0].title or slides[0].subtitle):
        return slides[0].title or slides[0].subtitle
    return Path(filepath).stem or DEFAULT_TITLE


class PresentationGenerator:
    """簡報生成器"""
    
    def __init__(self, presentation: Optional[Presentation] = None):
        self.presentation = presentation or Presentation()
        self.source_path: Optional[str] = None
        # 最近一次生成的警告（已含位置），供 watch 模式顯示
        self.warnings: List[str] = []
    
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
            # 沒有來源檔（程式直接建立的投影片）
            location = f'投影片 {slide_index + 1} 第 {line_index + 1} 行'
        warning = f'{location}: {message}'
        self.warnings.append(warning)
        print(warning, file=sys.stderr)
    
    def generate_html(self, output_path: str, template_path: Optional[str] = None) -> None:
        """生成 HTML 簡報並寫入檔案"""
        html = self.render_html(template_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def render_html(self, template_path: Optional[str] = None) -> str:
        """生成 HTML 簡報，回傳內容"""
        self.warnings = []
        # 使用預設模板或自訂模板
        if template_path is None:
            template_path = Path(__file__).parent / 'templates' / 'template.html'
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        template = Template(template_content)
        
        # 渲染每張投影片
        renderer = HTMLRenderer(warn=self._warn)
        slide_htmls = []
        
        for i, slide in enumerate(self.presentation.slides):
            slide_html = renderer.render_slide(slide, i)
            slide_htmls.append(slide_html)
        
        # 組合最終 HTML
        return template.render(
            title=self.presentation.title,
            slides=slide_htmls,
        )
