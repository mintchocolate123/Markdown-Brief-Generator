#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
html_renderer.py - 將投影片內容渲染為 HTML
"""

import re
from typing import Dict, List, Any
from markdown_parser import MarkdownParser
from syntax_highlighter import SyntaxHighlighter
from slide_model import Slide, SlideTheme


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
            parsed = self._parse_line_format(line)
            html_lines.append(self._render_formatted_line(parsed))
        
        return ''.join(html_lines)
    
    def _parse_line_format(self, line: str) -> Dict[str, Any]:
        """解析行的格式標記（支援連續多個標記）"""
        result = {
            'text': line,
            'cont': False,
            'is_subtitle': False,
            'is_important': False,
            'indent': 0,
            'align': None,
            'link': None,
            'image': None,
            'styles': {},
        }
        
        text = line.strip()
        if not text:
            return result
        
        # 持續解析所有開頭的格式標記
        while text.startswith('<') or text.startswith('['):
            start_char = text[0]
            end_char = '>' if start_char == '<' else ']'
            
            # 找到這個標記的結束位置
            depth = 0
            end = -1
            
            for i, c in enumerate(text):
                if c == start_char:
                    depth += 1
                elif c == end_char:
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            
            if end == -1:
                break  # 沒找到匹配的結束符，停止解析
            
            # 提取這個標記的內容
            fmt = text[1:end]
            text = text[end+1:].strip()  # 剩餘文本
            
            # 解析這個標記
            self._apply_format_token(fmt, result)
        
        result['text'] = text
        return result
    
    def _apply_format_token(self, fmt: str, result: Dict[str, Any]) -> None:
        """應用單個格式標記到結果"""
        # 解析格式標記中的tokens
        tokens = re.split(r'[<>\s]+', fmt)
        tokens = [t for t in tokens if t]  # 移除空字串
        
        # cont
        if 'cont' in tokens:
            result['cont'] = True
        
        # ct (content title/subtitle)
        if 'ct' in tokens:
            result['is_subtitle'] = True
        
        # imp (important)
        if 'imp' in tokens:
            result['is_important'] = True
        
        # 縮排
        tab_match = re.search(r'tab<(\d+)>', fmt)
        if tab_match:
            result['indent'] = int(tab_match.group(1))
        
        # 對齊
        pivot_match = re.search(r'pivot<([lcr])>', fmt)
        if pivot_match:
            pivot_map = {'l': 'left', 'c': 'center', 'r': 'right'}
            result['align'] = pivot_map.get(pivot_match.group(1))
        
        # 超連結
        link_match = re.search(r'link<([^>]+)>', fmt)
        if link_match:
            result['link'] = link_match.group(1)
        
        # 圖片
        img_match = re.search(r'img<([^,]+),([^,]+),([^>]+)>', fmt)
        if img_match:
            result['image'] = {
                'url': img_match.group(1),
                'width': img_match.group(2),
                'height': img_match.group(3),
            }
        
        # 字體大小
        size_match = re.search(r'size<(\d)>', fmt)
        if size_match:
            size_map = {
                '1': '0.7em', '2': '0.85em', '3': '1em',
                '4': '1.2em', '5': '1.5em', '6': '2em', '7': '2.5em'
            }
            size = size_match.group(1)
            if size in size_map:
                result['styles']['font-size'] = size_map[size]
        
        # 顏色
        color_match = re.search(r'color<([^>]+)>', fmt)
        if color_match:
            result['styles']['color'] = self._normalize_color(color_match.group(1))
        
        # 粗體
        if 'b' in tokens or 'bold' in tokens:
            result['styles']['font-weight'] = 'bold'
        
        # 斜體
        if 'i' in tokens or 'italic' in tokens:
            result['styles']['font-style'] = 'italic'
        
        # 底線和刪除線
        underline = 'u' in tokens or 'underline' in tokens
        strike = 's' in tokens or 'strike' in tokens
        
        if underline and strike:
            result['styles']['text-decoration'] = 'underline line-through'
        elif underline:
            result['styles']['text-decoration'] = 'underline'
        elif strike:
            result['styles']['text-decoration'] = 'line-through'
    
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
                parsed = self._parse_cell_format(cell)
                
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
    
    def _parse_cell_format(self, text: str) -> Dict[str, Any]:
        """解析表格儲存格格式"""
        result = {
            'text': text,
            'imp': False,
            'styles': {},
        }
        
        stripped = text.strip()
        if not stripped.startswith('<'):
            return result
        
        # 找到格式區塊結束位置
        depth = 0
        end = -1
        for i, c in enumerate(stripped):
            if c == '<':
                depth += 1
            elif c == '>':
                depth -= 1
            if depth == 0:
                end = i
                break
        
        if end == -1:
            return result
        
        fmt = stripped[1:end]
        result['text'] = stripped[end+1:]
        
        if 'imp' in fmt.split():
            result['imp'] = True
        
        # 字體大小
        size_match = re.search(r'size<(\d)>', fmt)
        if size_match:
            size_map = {
                '1': '0.7em', '2': '0.85em', '3': '1em',
                '4': '1.2em', '5': '1.5em', '6': '2em', '7': '2.5em'
            }
            size = size_match.group(1)
            if size in size_map:
                result['styles']['font-size'] = size_map[size]
        
        # 顏色
        color_match = re.search(r'color<([^>]+)>', fmt)
        if color_match:
            result['styles']['color'] = self._normalize_color(color_match.group(1))
        
        # 粗體
        if 'b' in fmt.split() or 'bold' in fmt.split():
            result['styles']['font-weight'] = 'bold'
        
        # 斜體
        if 'i' in fmt.split() or 'italic' in fmt.split():
            result['styles']['font-style'] = 'italic'
        
        # 底線和刪除線
        underline = 'u' in fmt.split() or 'underline' in fmt.split()
        strike = 's' in fmt.split() or 'strike' in fmt.split()
        
        if underline and strike:
            result['styles']['text-decoration'] = 'underline line-through'
        elif underline:
            result['styles']['text-decoration'] = 'underline'
        elif strike:
            result['styles']['text-decoration'] = 'line-through'
        
        return result
    
    def _normalize_color(self, color: str) -> str:
        """標準化顏色值"""
        color_map = {
            'black': '#000', 'white': '#fff',
            'red': '#f00', 'green': '#008000', 'blue': '#00f',
            'yellow': '#ff0', 'cyan': '#0ff',
            'orange': '#ffa500', 'purple': '#800080',
            'pink': '#ffc0cb', 'gray': '#808080',
        }
        return color_map.get(color.strip().lower(), color)
    
    def _escape_html(self, text: str) -> str:
        """HTML 轉義"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
