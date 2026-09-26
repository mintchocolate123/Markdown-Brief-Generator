#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
blocks.py - Markdown 區塊解析器
支援擴展語法：表格、程式碼區塊、樹狀圖等
"""

import re
from typing import Dict, List, Tuple, Any, Optional

from briefgen.tags import parse_format, split_token, split_top_level


WIDTH_RE = re.compile(r'\[width=([^\]]+)\]')
TREE_NODE_NAMES = {'id', 'p'}


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
        self.warnings = []  # (行索引, 訊息)
    
    def normalize_lang(self, lang: str) -> str:
        """標準化語言名稱"""
        lang = lang.lower().strip()
        return self.LANG_NORMALIZE.get(lang, lang)
    
    def is_supported_lang(self, lang: str) -> bool:
        """檢查是否支援該語言的語法高亮"""
        return self.normalize_lang(lang) in self.SUPPORTED_LANGS
    
    def parse(self, content: str) -> Tuple[str, List[Dict[str, Any]], List[int]]:
        """
        解析 Markdown 內容，提取特殊區塊
        
        返回:
            - 處理後的文本（特殊區塊用佔位符取代）
            - 區塊列表
            - 處理後每一行對應的原始行索引
        """
        self.blocks = []
        self.warnings = []
        lines = content.split('\n')
        result = []
        line_map = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            block = None
            # 程式碼區塊（Markdown 標準格式）、表格區塊、樹狀圖區塊
            if stripped.startswith('```'):
                block, end_index = self._parse_code_block(lines, i)
            elif stripped == '[table]':
                block, end_index = self._parse_table_block(lines, i)
            elif stripped == '[tree]':
                block, end_index = self._parse_tree_block(lines, i)
            
            if block:
                key = f"{block['type']}_{len(self.blocks)}"
                self.blocks.append({**block, 'key': key})
                result.append(f'[BLOCK_REF:{key}]')
                line_map.append(i)
                i = end_index + 1
                continue
            
            result.append(line)
            line_map.append(i)
            i += 1
        
        return '\n'.join(result), self.blocks, line_map
    
    def _parse_width(self, line: str) -> Optional[str]:
        """解析 [width=...] 設定行"""
        width_match = WIDTH_RE.match(line.strip())
        if not width_match:
            return None
        return split_token('width=' + width_match.group(1))[1]
    
    def _collect_block(self, lines: List[str], start: int, closer: str) -> Tuple[Optional[List[Tuple[int, str]]], Optional[str], int]:
        """收集區塊內的資料行（含原始行索引）與寬度設定，找不到結束標記時回傳 None"""
        data_lines = []
        width = None
        
        i = start + 1
        while i < len(lines):
            line = lines[i]
            
            # 檢查結束標記
            if line.strip() == closer:
                return data_lines, width, i
            
            # 檢查寬度設定
            line_width = self._parse_width(line)
            if line_width is not None:
                width = line_width
                i += 1
                continue
            
            data_lines.append((i, line))
            i += 1
        
        return None, None, start
    
    def _parse_code_block(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """解析程式碼區塊"""
        first_line = lines[start].strip()
        
        # 提取語言標識
        lang_match = re.match(r'```(\w+)?', first_line)
        lang = lang_match.group(1) if lang_match and lang_match.group(1) else 'text'
        
        data_lines, width, end = self._collect_block(lines, start, '```')
        if data_lines is None:
            return None, start
        
        return {
            'type': 'code',
            'lang': self.normalize_lang(lang),
            'code': '\n'.join(line for _, line in data_lines),
            'width': width,
        }, end
    
    def _parse_table_block(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """解析表格區塊"""
        data_lines, width, end = self._collect_block(lines, start, '[/table]')
        if data_lines is None:
            return None, start
        
        rows, cell_lines = self._parse_table_data(data_lines)
        return {
            'type': 'table',
            'data': rows,
            'cell_lines': cell_lines,
            'width': width,
        }, end
    
    def _parse_table_data(self, lines: List[Tuple[int, str]]) -> Tuple[List[List[str]], List[List[int]]]:
        """解析表格資料，另回傳每個儲存格的原始行索引"""
        rows = []
        cell_lines = []
        current_cells = []
        current_lines = []
        
        for index, line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # 新儲存格標記
            if stripped.startswith('[c]'):
                current_cells.append(stripped[3:])
                current_lines.append(index)
            else:
                # 新一行
                if current_cells:
                    rows.append(current_cells)
                    cell_lines.append(current_lines)
                current_cells = [stripped]
                current_lines = [index]
        
        if current_cells:
            rows.append(current_cells)
            cell_lines.append(current_lines)
        
        return rows, cell_lines
    
    def _parse_tree_block(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """解析樹狀圖區塊"""
        data_lines, width, end = self._collect_block(lines, start, '[/tree]')
        if data_lines is None:
            return None, start
        
        return {
            'type': 'tree',
            'data': self._parse_tree_data(data_lines),
            'width': width,
        }, end
    
    def _parse_tree_data(self, lines: List[Tuple[int, str]]) -> List[Dict[str, Any]]:
        """解析樹狀圖資料：[id=X p=Y] 文字"""
        nodes = []
        
        for index, line in lines:
            stripped = line.strip()
            if not stripped.startswith('['):
                continue
            
            end = stripped.find(']')
            if end == -1:
                continue
            
            node = {
                'id': None,
                'parent': None,
                'text': '',
                'styles': {},
                'line': index,
            }
            
            for token in split_top_level(stripped[1:end]):
                name, value = split_token(token)
                if name in TREE_NODE_NAMES and value:
                    node['id' if name == 'id' else 'parent'] = value
                else:
                    self.warnings.append((index, f'樹節點不認識的設定：{token}'))
            
            # 解析文本樣式
            text_parsed = parse_format(stripped[end+1:])
            for warning in text_parsed['warnings']:
                self.warnings.append((index, warning))
            if text_parsed['cont']:
                self.warnings.append((index, '樹節點不支援 cont，已忽略'))
                text_parsed['text'] = text_parsed['text'].strip()
            node['text'] = text_parsed['text']
            node['styles'] = text_parsed['styles']
            
            nodes.append(node)
        
        return nodes
