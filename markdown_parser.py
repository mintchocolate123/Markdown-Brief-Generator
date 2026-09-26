#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
markdown_parser.py - Markdown 內容解析器
支援擴展語法：表格、程式碼區塊、樹狀圖等
"""

import re
from typing import Dict, List, Tuple, Any, Optional


class MarkdownParser:
    """擴展的 Markdown 解析器"""
    
    # 支援的程式語言
    SUPPORTED_LANGS = {
        'c', 'cpp', 'c++', 'cs', 'c#', 
        'py', 'python', 'js', 'javascript', 'java'
    }
    
    # 語言標準化映射
    LANG_NORMALIZE = {
        'c++': 'cpp',
        'c#': 'cs',
        'python': 'py',
        'javascript': 'js',
    }
    
    def __init__(self):
        self.blocks = []
    
    def normalize_lang(self, lang: str) -> str:
        """標準化語言名稱"""
        lang = lang.lower().strip()
        return self.LANG_NORMALIZE.get(lang, lang)
    
    def is_supported_lang(self, lang: str) -> bool:
        """檢查是否支援該語言的語法高亮"""
        return self.normalize_lang(lang) in self.SUPPORTED_LANGS
    
    def parse(self, content: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        解析 Markdown 內容，提取特殊區塊
        
        返回:
            - 處理後的文本（特殊區塊用佔位符取代）
            - 區塊列表
        """
        self.blocks = []
        lines = content.split('\n')
        result = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 檢查是否為程式碼區塊（Markdown 標準格式）
            if line.strip().startswith('```'):
                block, end_index = self._parse_code_block(lines, i)
                if block:
                    key = f"code_{len(self.blocks)}"
                    self.blocks.append({**block, 'key': key})
                    result.append(f'[BLOCK_REF:{key}]')
                    i = end_index + 1
                    continue
            
            # 檢查是否為表格區塊
            if line.strip() == '[table]':
                block, end_index = self._parse_table_block(lines, i)
                if block:
                    key = f"table_{len(self.blocks)}"
                    self.blocks.append({**block, 'key': key})
                    result.append(f'[BLOCK_REF:{key}]')
                    i = end_index + 1
                    continue
            
            # 檢查是否為樹狀圖區塊
            if line.strip() == '[tree]':
                block, end_index = self._parse_tree_block(lines, i)
                if block:
                    key = f"tree_{len(self.blocks)}"
                    self.blocks.append({**block, 'key': key})
                    result.append(f'[BLOCK_REF:{key}]')
                    i = end_index + 1
                    continue
            
            result.append(line)
            i += 1
        
        return '\n'.join(result), self.blocks
    
    def _parse_code_block(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """解析程式碼區塊"""
        first_line = lines[start].strip()
        
        # 提取語言標識
        lang_match = re.match(r'```(\w+)?', first_line)
        lang = lang_match.group(1) if lang_match and lang_match.group(1) else 'text'
        
        code_lines = []
        width = None
        
        i = start + 1
        while i < len(lines):
            line = lines[i]
            
            # 檢查結束標記
            if line.strip() == '```':
                return {
                    'type': 'code',
                    'lang': self.normalize_lang(lang),
                    'code': '\n'.join(code_lines),
                    'width': width,
                }, i
            
            # 檢查寬度設定
            width_match = re.match(r'\[width<([^>]+)>\]', line.strip())
            if width_match:
                width = width_match.group(1)
                i += 1
                continue
            
            code_lines.append(line)
            i += 1
        
        return None, start
    
    def _parse_table_block(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """解析表格區塊"""
        data_lines = []
        width = None
        
        i = start + 1
        while i < len(lines):
            line = lines[i]
            
            # 檢查結束標記
            if line.strip() == '[/table]':
                rows = self._parse_table_data(data_lines)
                return {
                    'type': 'table',
                    'data': rows,
                    'width': width,
                }, i
            
            # 檢查寬度設定
            width_match = re.match(r'\[width<([^>]+)>\]', line.strip())
            if width_match:
                width = width_match.group(1)
                i += 1
                continue
            
            data_lines.append(line)
            i += 1
        
        return None, start
    
    def _parse_table_data(self, lines: List[str]) -> List[List[str]]:
        """解析表格資料"""
        rows = []
        current_cells = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # 新儲存格標記
            if stripped == '[c]':
                current_cells.append('')
            elif stripped.startswith('[c]'):
                current_cells.append(stripped[3:])
            else:
                # 新一行
                if current_cells:
                    rows.append(current_cells)
                current_cells = [stripped]
        
        if current_cells:
            rows.append(current_cells)
        
        return rows
    
    def _parse_tree_block(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """解析樹狀圖區塊"""
        data_lines = []
        width = None
        
        i = start + 1
        while i < len(lines):
            line = lines[i]
            
            # 檢查結束標記
            if line.strip() == '[/tree]':
                nodes = self._parse_tree_data(data_lines)
                return {
                    'type': 'tree',
                    'data': nodes,
                    'width': width,
                }, i
            
            # 檢查寬度設定
            width_match = re.match(r'\[width<([^>]+)>\]', line.strip())
            if width_match:
                width = width_match.group(1)
                i += 1
                continue
            
            data_lines.append(line)
            i += 1
        
        return None, start
    
    def _parse_tree_data(self, lines: List[str]) -> List[Dict[str, Any]]:
        """解析樹狀圖資料"""
        nodes = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped or not stripped.startswith('['):
                continue
            
            node = {
                'id': None,
                'parent': None,
                'order': None,
                'total': None,
                'text': '',
                'styles': {},
                'imp': False,
            }
            
            # 找到格式區塊的結束位置
            depth = 0
            end = -1
            for i, c in enumerate(stripped):
                if c == '[':
                    depth += 1
                elif c == ']':
                    depth -= 1
                if depth == 0:
                    end = i
                    break
            
            if end == -1:
                continue
            
            fmt = stripped[1:end]
            text = stripped[end+1:].strip()
            
            # 解析格式標記
            id_match = re.search(r'id<([^>]+)>', fmt)
            if id_match:
                node['id'] = id_match.group(1)
            
            parent_match = re.search(r'p<([^>]+)>', fmt)
            if parent_match:
                node['parent'] = parent_match.group(1)
            
            order_match = re.search(r'o<(\d+)/(\d+)>', fmt)
            if order_match:
                node['order'] = int(order_match.group(1))
                node['total'] = int(order_match.group(2))
            
            if 'imp' in fmt.split():
                node['imp'] = True
            
            # 解析文本樣式
            text_parsed = self._parse_inline_format(text)
            node['text'] = text_parsed['text']
            node['styles'] = text_parsed['styles']
            
            nodes.append(node)
        
        return nodes
    
    def _parse_inline_format(self, text: str) -> Dict[str, Any]:
        """解析行內格式標記"""
        result = {
            'text': text,
            'styles': {},
            'imp': False,
        }
        
        if not text.startswith('<'):
            return result
        
        # 找到格式區塊結束
        depth = 0
        end = -1
        for i, c in enumerate(text):
            if c == '<':
                depth += 1
            elif c == '>':
                depth -= 1
            if depth == 0:
                end = i
                break
        
        if end == -1:
            return result
        
        fmt = text[1:end]
        result['text'] = text[end+1:]
        
        # 解析各種格式
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
