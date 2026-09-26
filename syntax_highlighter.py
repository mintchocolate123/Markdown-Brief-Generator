#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
syntax_highlighter.py - 程式碼語法高亮
"""

import re
from typing import Dict, Tuple


class SyntaxHighlighter:
    """程式碼語法高亮器"""
    
    # 各語言的配色方案
    LANG_COLORS = {
        'c': {
            'kw': '#569cd6',
            'str': '#ce9178',
            'cmt': '#6a9955',
            'num': '#b5cea8',
            'bg': '#1e1e1e',
        },
        'cpp': {
            'kw': '#569cd6',
            'str': '#ce9178',
            'cmt': '#6a9955',
            'num': '#b5cea8',
            'bg': '#1e1e1e',
        },
        'cs': {
            'kw': '#569cd6',
            'str': '#ce9178',
            'cmt': '#6a9955',
            'num': '#b5cea8',
            'bg': '#1e1e1e',
        },
        'py': {
            'kw': '#ff79c6',
            'str': '#f1fa8c',
            'cmt': '#6272a4',
            'num': '#bd93f9',
            'bg': '#282a36',
        },
        'js': {
            'kw': '#c586c0',
            'str': '#ce9178',
            'cmt': '#6a9955',
            'num': '#b5cea8',
            'bg': '#1e1e1e',
        },
        'java': {
            'kw': '#cc7832',
            'str': '#6a8759',
            'cmt': '#808080',
            'num': '#6897bb',
            'bg': '#2b2b2b',
        },
    }
    
    # 各語言的關鍵字
    LANG_KEYWORDS = {
        'c': [
            'int', 'float', 'double', 'char', 'void',
            'if', 'else', 'for', 'while', 'return',
            'include', 'define', 'printf', 'scanf',
            'NULL', 'struct', 'typedef', 'sizeof',
        ],
        'cpp': [
            'int', 'float', 'double', 'char', 'void',
            'if', 'else', 'for', 'while', 'return',
            'include', 'define', 'class', 'public', 'private',
            'new', 'delete', 'cout', 'cin', 'endl',
            'string', 'vector', 'using', 'namespace', 'std',
            'nullptr', 'bool', 'true', 'false',
            'template', 'typename',
        ],
        'cs': [
            'int', 'float', 'double', 'string', 'void',
            'if', 'else', 'for', 'while', 'return',
            'class', 'public', 'private', 'new', 'null',
            'bool', 'true', 'false', 'using', 'namespace',
            'var', 'async', 'await', 'Console', 'WriteLine', 'static',
        ],
        'py': [
            'def', 'class', 'if', 'elif', 'else',
            'for', 'while', 'return', 'import', 'from',
            'True', 'False', 'None', 'and', 'or', 'not',
            'in', 'is', 'print', 'input', 'len', 'range',
            'self', 'async', 'await', 'with', 'try', 'except',
            'lambda', 'pass', 'break', 'continue',
        ],
        'js': [
            'var', 'let', 'const', 'function',
            'if', 'else', 'for', 'while', 'return',
            'true', 'false', 'null', 'undefined',
            'class', 'new', 'this', 'async', 'await',
            'console', 'log', 'import', 'export', 'from', 'Promise',
        ],
        'java': [
            'int', 'float', 'double', 'String', 'void',
            'if', 'else', 'for', 'while', 'return',
            'class', 'public', 'private', 'new', 'null',
            'boolean', 'true', 'false', 'import', 'package',
            'static', 'System', 'out', 'println',
            'final', 'abstract', 'extends', 'implements',
        ],
    }
    
    def highlight(self, code: str, lang: str) -> Tuple[str, str]:
        """
        高亮程式碼
        
        返回:
            - 高亮後的 HTML
            - 背景色
        """
        # HTML 轉義
        code = code.replace('&', '&amp;')
        code = code.replace('<', '&lt;')
        code = code.replace('>', '&gt;')
        
        # 檢查是否支援該語言
        if lang not in self.LANG_COLORS:
            return code, '#2d2d2d'
        
        colors = self.LANG_COLORS[lang]
        keywords = self.LANG_KEYWORDS.get(lang, [])
        
        # 使用佔位符保護已處理的內容
        placeholders = []
        
        def save_placeholder(match, color):
            """儲存佔位符"""
            placeholder_id = len(placeholders)
            html = f'<span style="color:{color}">{match.group(0)}</span>'
            placeholders.append(html)
            return f'\x00\x01{placeholder_id}\x01\x00'
        
        # 1. 處理字串（最高優先級）
        code = re.sub(
            r'"[^"\\]*(?:\\.[^"\\]*)*"',
            lambda m: save_placeholder(m, colors['str']),
            code
        )
        code = re.sub(
            r"'[^'\\]*(?:\\.[^'\\]*)*'",
            lambda m: save_placeholder(m, colors['str']),
            code
        )
        
        # 2. 處理註解
        code = re.sub(
            r'//.*$',
            lambda m: save_placeholder(m, colors['cmt']),
            code,
            flags=re.MULTILINE
        )
        
        if lang == 'py':
            code = re.sub(
                r'#.*$',
                lambda m: save_placeholder(m, colors['cmt']),
                code,
                flags=re.MULTILINE
            )
        
        # 3. 處理數字
        code = re.sub(
            r'(?<!\x01)\b\d+\.?\d*\b(?!\x01)',
            lambda m: f'<span style="color:{colors["num"]}">{m.group(0)}</span>',
            code
        )
        
        # 4. 處理關鍵字
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            replacement = f'<span style="color:{colors["kw"]};font-weight:bold">{keyword}</span>'
            code = re.sub(pattern, replacement, code)
        
        # 5. 還原佔位符
        for i, placeholder_html in enumerate(placeholders):
            code = code.replace(f'\x00\x01{i}\x01\x00', placeholder_html)
        
        return code, colors['bg']
