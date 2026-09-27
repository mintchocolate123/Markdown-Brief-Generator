#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
highlighter.py - 程式碼語法高亮
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
        'bash': {
            'kw': '#569cd6',
            'str': '#ce9178',
            'cmt': '#6a9955',
            'num': '#b5cea8',
            'var': '#9cdcfe',
            'bg': '#1e1e1e',
        },
        'html': {
            'kw': '#569cd6',
            'str': '#ce9178',
            'cmt': '#6a9955',
            'num': '#b5cea8',
            'attr': '#9cdcfe',
            'bg': '#1e1e1e',
        },
        'css': {
            'kw': '#d7ba7d',
            'str': '#ce9178',
            'cmt': '#6a9955',
            'num': '#b5cea8',
            'attr': '#9cdcfe',
            'bg': '#1e1e1e',
        },
        'json': {
            'kw': '#569cd6',
            'str': '#ce9178',
            'cmt': '#6a9955',
            'num': '#b5cea8',
            'attr': '#9cdcfe',
            'bg': '#1e1e1e',
        },
    }
    
    # 各語言依序套用的規則：(正規表示式, 顏色, flags)；規則比對的是 HTML 轉義後的程式碼
    DOUBLE_QUOTED = (r'"[^"\\]*(?:\\.[^"\\]*)*"', 'str', 0)
    SINGLE_QUOTED = (r"'[^'\\]*(?:\\.[^'\\]*)*'", 'str', 0)
    LINE_COMMENT = (r'//.*$', 'cmt', re.MULTILINE)
    HASH_COMMENT = (r'#.*$', 'cmt', re.MULTILINE)
    BLOCK_COMMENT = (r'/\*.*?\*/', 'cmt', re.DOTALL)
    
    LANG_RULES = {
        'c': [DOUBLE_QUOTED, SINGLE_QUOTED, LINE_COMMENT],
        'cpp': [DOUBLE_QUOTED, SINGLE_QUOTED, LINE_COMMENT],
        'cs': [DOUBLE_QUOTED, SINGLE_QUOTED, LINE_COMMENT],
        'js': [DOUBLE_QUOTED, SINGLE_QUOTED, LINE_COMMENT],
        'java': [DOUBLE_QUOTED, SINGLE_QUOTED, LINE_COMMENT],
        'py': [DOUBLE_QUOTED, SINGLE_QUOTED, HASH_COMMENT],
        'bash': [
            DOUBLE_QUOTED, SINGLE_QUOTED,
            (r'(?<![\w$])#.*$', 'cmt', re.MULTILINE),
            (r'\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|\$[0-9@#?*]', 'var', 0),
        ],
        'html': [
            (r'&lt;!--.*?--&gt;', 'cmt', re.DOTALL),
            DOUBLE_QUOTED, SINGLE_QUOTED,
            (r'(?<=&lt;)/?[A-Za-z][\w-]*', 'kw', 0),
            (r'[A-Za-z_:][\w:.-]*(?==)', 'attr', 0),
        ],
        'css': [
            BLOCK_COMMENT, DOUBLE_QUOTED, SINGLE_QUOTED,
            (r'^\s*[\w-]+(?=\s*:(?![^\n]*\{))', 'attr', re.MULTILINE),
            (r'#[0-9A-Fa-f]{3,8}\b', 'num', 0),
            # 數值與單位（排除佔位符 \x01編號\x01 裡的數字）
            (r'(?<![\w#.\x01-])-?\d*\.?\d+(?:[A-Za-z]+|%)?(?!\x01)', 'num', 0),
            (r'^[^{}\n]+(?=\{)', 'kw', re.MULTILINE),
        ],
        'json': [
            (r'"[^"\\]*(?:\\.[^"\\]*)*"(?=\s*:)', 'attr', 0),
            DOUBLE_QUOTED,
        ],
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
        'bash': [
            'if', 'then', 'else', 'elif', 'fi', 'for', 'while', 'until',
            'do', 'done', 'case', 'esac', 'in', 'function', 'return',
            'echo', 'export', 'local', 'source', 'exit', 'cd',
        ],
        'json': ['true', 'false', 'null'],
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
        
        # 1-2. 依序處理字串、註解等（以佔位符保護，後面的規則不會再改到）
        for pattern, color, flags in self.LANG_RULES[lang]:
            code = re.sub(
                pattern,
                lambda m, color=color: save_placeholder(m, colors[color]),
                code,
                flags=flags
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
