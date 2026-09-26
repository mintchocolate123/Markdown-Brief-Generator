#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
html_renderer.py - 將投影片內容渲染為 HTML
"""

import re
from typing import Dict, List, Any
from briefgen.parsing.blocks import MarkdownParser
from briefgen.highlighter import SyntaxHighlighter
from briefgen.model import Slide, SlideTheme
from briefgen.tags import parse_line_format, parse_cell_format


class HTMLRenderer:
    """HTML 渲染器"""
    
    def __init__(self, theme: SlideTheme):
        self.theme = theme
        self.parser = MarkdownParser()
        self.highlighter = SyntaxHighlighter()
    
    def render_slide(self, slide: Slide, index: int) -> str:
        """渲染單張投影片為獨立的 HTML"""
        # 解析 Markdown 內容
        content, blocks = self.parser.parse(slide.content)
        
        # 建立區塊映射
        block_map = {block['key']: block for block in blocks}
        
        # 渲染主要內容
        content_html = self._render_content(content, block_map)
        
        # 組裝投影片 HTML（符合原始格式）
        slide_id = f'slide{index + 1}'
        
        # 如果有標題就加 slide-header
        if slide.title:
            html = f'<div class="slide" id="{slide_id}"><div class="slide-header"><h1>{self._escape_html(slide.title)}</h1><p class="subtitle">{self._escape_html(slide.subtitle) if slide.subtitle else ""}</p></div><div class="slide-content">{content_html}</div></div>'
        else:
            html = f'<div class="slide" id="{slide_id}"><div class="slide-content">{content_html}</div></div>'
        
        return html
    
    def _render_content(self, content: str, block_map: Dict[str, Dict]) -> str:
        """渲染內容文本"""
        lines = content.split('\n')
        result = []
        paragraph = []
        
        for line in lines:
            stripped = line.strip()
            
            # 區塊引用
            if stripped.startswith('[BLOCK_REF:'):
                if paragraph:
                    result.append(self._render_paragraph(paragraph))
                    paragraph = []
                
                key = re.search(r'\[BLOCK_REF:([^\]]+)\]', stripped).group(1)
                if key in block_map:
                    result.append(self._render_block(block_map[key]))
                continue
            
            # 空行分段
            if not stripped:
                if paragraph:
                    result.append(self._render_paragraph(paragraph))
                    paragraph = []
                continue
            
            paragraph.append(line)
        
        if paragraph:
            result.append(self._render_paragraph(paragraph))
        
        return '\n'.join(result)
    
    def _render_paragraph(self, lines: List[str]) -> str:
        """渲染段落"""
        html_lines = []
        
        for line in lines:
            parsed = parse_line_format(line)
            html_lines.append(self._render_formatted_line(parsed))
        
        return ''.join(html_lines)
    
    def _render_formatted_line(self, parsed: Dict[str, Any]) -> str:
        """渲染格式化的行"""
        # 處理圖片
        if parsed['image']:
            img = parsed['image']
            return f'<div><img src="{img["url"]}" style="max-width:100%;border-radius:10px;"></div>'
        
        # 建立樣式字串
        style_parts = []
        
        # 子標題樣式
        if parsed['is_subtitle']:
            style_parts.append('font-size:1.4em')
            style_parts.append('font-weight:bold')
            style_parts.append('color:#feca57')
            style_parts.append('border-bottom:2px solid #feca57')
            style_parts.append('padding-bottom:5px')
            style_parts.append('margin-bottom:10px')
            style_parts.append('display:inline-block')
        
        # 重要區塊樣式
        if parsed['is_important']:
            style_parts.append('text-align:center')
            style_parts.append('border:2px solid #feca57')
            style_parts.append('border-radius:10px')
            style_parts.append('padding:15px 20px')
            style_parts.append('background:rgba(254,202,87,.1)')
            style_parts.append('margin:10px 0')
        
        # 縮排
        if parsed['indent'] > 0:
            style_parts.append(f'margin-left:{parsed["indent"] * 2}em')
        
        # 對齊
        if parsed['align']:
            style_parts.append(f'text-align:{parsed["align"]}')
        
        # 自訂樣式
        for key, value in parsed['styles'].items():
            style_parts.append(f'{key}:{value}')
        
        style_str = ';'.join(style_parts) if style_parts else ''
        
        # 文本內容
        text = self._escape_html(parsed['text'])
        
        # 超連結
        if parsed['link']:
            text = f'<a href="{parsed["link"]}" target="_blank" style="color:#feca57;text-decoration:underline;">{text}</a>'
        
        # 包裝樣式
        if parsed['is_subtitle']:
            # 子標題需要額外包裝
            return f'<div style="display:flex;align-items:flex-end;flex-wrap:wrap;gap:10px"><span style="{style_str}">{text}</span></div>'
        
        # 組裝 HTML
        if style_str:
            return f'<div style="{style_str}">{text}</div>'
        else:
            return f'<div>{text}</div>'
    
    def _render_block(self, block: Dict[str, Any]) -> str:
        """渲染特殊區塊"""
        block_type = block['type']
        
        if block_type == 'code':
            return self._render_code_block(block)
        elif block_type == 'table':
            return self._render_table_block(block)
        elif block_type == 'tree':
            return self._render_tree_block(block)
        
        return ''
    
    def _render_code_block(self, block: Dict[str, Any]) -> str:
        """渲染程式碼區塊"""
        code = block['code']
        lang = block['lang']
        width = block.get('width')
        
        # 語法高亮
        highlighted, bg_color = self.highlighter.highlight(code, lang)
        
        # 語言標籤顯示
        lang_display = lang.upper()
        
        # 生成唯一 ID 供複製功能使用
        import hashlib
        code_id = hashlib.md5(code.encode()).hexdigest()[:8]
        
        # 儲存原始程式碼（轉義後）供複製使用
        code_escaped = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
        
        # 組裝完整 HTML（符合原始格式 + 複製按鈕）
        html = f'<div style="background:{bg_color};padding:15px 18px;border-radius:10px;font-family:Consolas,Monaco,monospace;font-size:0.9em;display:block;margin:8px 0;border-left:4px solid #feca57;overflow-x:auto;position:relative;'
        
        if width == 'full':
            html += 'width:100%;'
        elif width:
            html += f'min-width:{width};'
        
        html += f'">'
        
        # 頂部工具列（語言標籤 + 複製按鈕）
        html += f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
        html += f'<span style="background:#e94560;color:#fff;padding:3px 10px;border-radius:4px;font-size:0.7em;font-weight:bold;">{lang_display}</span>'
        html += f'<button onclick="copyCode(\'{code_id}\')" id="copyBtn{code_id}" style="background:#4ecdc4;color:#fff;border:none;padding:5px 12px;border-radius:4px;font-size:0.7em;cursor:pointer;font-weight:bold;transition:all 0.3s;">複製</button>'
        html += f'</div>'
        
        # 程式碼內容（隱藏的原始碼 + 顯示的高亮碼）
        html += f'<div style="display:none;" id="code{code_id}">{code_escaped}</div>'
        html += f'<pre style="margin:0;white-space:pre-wrap;word-break:break-all;line-height:1.6;color:#fff;">{highlighted}</pre>'
        html += f'</div>'
        
        return html
    
    def _render_table_block(self, block: Dict[str, Any]) -> str:
        """渲染表格區塊"""
        data = block['data']
        width = block.get('width')
        
        if not data:
            return ''
        
        # 寬度樣式
        width_style = 'width:100%;' if width == 'full' else (f'min-width:{width};' if width else 'width:100%;')
        
        # 渲染表格
        rows_html = []
        for row_idx, row in enumerate(data):
            cells_html = []
            for cell in row:
                parsed = parse_cell_format(cell)
                
                # 第一行或important的樣式
                if row_idx == 0 or parsed['imp']:
                    cell_style = 'padding:10px 15px;border:1px solid rgba(255,255,255,.2);text-align:center;background:linear-gradient(90deg,#e9456088,#ff6b6b88);font-weight:bold;'
                else:
                    cell_style = 'padding:10px 15px;border:1px solid rgba(255,255,255,.2);text-align:center;'
                
                # 加入自訂樣式
                for k, v in parsed['styles'].items():
                    cell_style += f'{k}:{v};'
                
                text = self._escape_html(parsed['text'])
                cells_html.append(f'<td style="{cell_style}">{text}</td>')
            
            rows_html.append(f'<tr>{"".join(cells_html)}</tr>')
        
        return f'<div><table style="border-collapse:collapse;background:rgba(255,255,255,.1);border-radius:10px;overflow:hidden;margin:5px 0;{width_style}">{"".join(rows_html)}</table></div>'
    
    def _render_tree_block(self, block: Dict[str, Any]) -> str:
        """渲染樹狀圖區塊"""
        nodes = block['data']
        width = block.get('width')
        
        if not nodes:
            return ''
        
        # 建立節點映射
        node_map = {node['id']: node for node in nodes if node['id']}
        
        # 找到根節點
        root_nodes = [node for node in nodes if not node['parent']]
        
        # 寬度樣式
        width_style = ''
        if width == 'full':
            width_style = 'width:100%;'
        
        # 渲染樹（使用原始的 flex 佈局）
        tree_html = self._render_tree_flex(root_nodes, node_map)
        
        return f'<div style="{width_style}">{tree_html}</div>'
    
    def _render_tree_flex(self, nodes: List[Dict], node_map: Dict) -> str:
        """使用 flex 布局渲染樹"""
        if not nodes or len(nodes) == 0:
            return ''
        
        html = '<div style="display:flex;flex-direction:column;align-items:center;margin:10px 0;">'
        
        for node_idx, node in enumerate(nodes):
            # 節點樣式
            node_style = 'background:rgba(255,255,255,.15);padding:8px 16px;border-radius:20px;display:inline-block;margin:5px;border:2px solid rgba(255,255,255,.3);'
            
            if node.get('imp'):
                node_style = 'background:rgba(255,255,255,.15);padding:8px 16px;border-radius:20px;display:inline-block;margin:5px;border:2px solid rgba(255,255,255,.3);'
            
            # 加入自訂樣式
            for k, v in node.get('styles', {}).items():
                node_style += f'{k}:{v};'
            
            text = self._escape_html(node.get('text', ''))
            
            # 找子節點
            children = [n for n in node_map.values() if n.get('parent') == node.get('id')]
            
            if children:
                # 有子節點 - 渲染階層結構
                html += '<div style="display:flex;flex-direction:column;align-items:center;">'
                html += f'<div style="{node_style}">{text}</div>'
                html += '<div style="width:2px;height:15px;background:rgba(255,255,255,.4)"></div>'
                html += '<div style="height:2px;background:rgba(255,255,255,.4);width:80%;max-width:200px"></div>'
                html += '<div style="display:flex;gap:20px">'
                
                for child in children:
                    html += '<div style="display:flex;flex-direction:column;align-items:center">'
                    html += '<div style="width:2px;height:15px;background:rgba(255,255,255,.4)"></div>'
                    
                    # 子節點樣式
                    child_style = 'background:rgba(255,255,255,.15);padding:8px 16px;border-radius:20px;display:inline-block;margin:5px;border:2px solid rgba(255,255,255,.3);'
                    child_text = self._escape_html(child.get('text', ''))
                    
                    html += f'<div style="display:flex;flex-direction:column;align-items:center;"><div style="{child_style}">{child_text}</div></div>'
                    html += '</div>'
                
                html += '</div>'
                html += '</div>'
            else:
                # 無子節點 - 單一節點
                html += f'<div style="{node_style}">{text}</div>'
        
        html += '</div>'
        return html
    
    def _escape_html(self, text: str) -> str:
        """HTML 轉義"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
