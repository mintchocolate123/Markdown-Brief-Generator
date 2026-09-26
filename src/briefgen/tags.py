#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tags.py - 行首格式標記解析（行內文字、表格儲存格、樹節點共用）
"""

import re
from typing import Any, Callable, Dict, List


SIZE_MAP = {
    '1': '0.7em', '2': '0.85em', '3': '1em',
    '4': '1.2em', '5': '1.5em', '6': '2em', '7': '2.5em'
}

PIVOT_MAP = {'l': 'left', 'c': 'center', 'r': 'right'}

COLOR_MAP = {
    'black': '#000', 'white': '#fff',
    'red': '#f00', 'green': '#008000', 'blue': '#00f',
    'yellow': '#ff0', 'cyan': '#0ff',
    'orange': '#ffa500', 'purple': '#800080',
    'pink': '#ffc0cb', 'gray': '#808080',
}


def normalize_color(color: str) -> str:
    """標準化顏色值"""
    return COLOR_MAP.get(color.strip().lower(), color)


def split_tokens_regex(fmt: str) -> List[str]:
    """以角括號與空白切割（行內文字）"""
    return [t for t in re.split(r'[<>\s]+', fmt) if t]


def split_tokens_whitespace(fmt: str) -> List[str]:
    """只以空白切割（儲存格、樹節點）"""
    return fmt.split()


def find_tag_end(text: str) -> int:
    """找到開頭標記對應的結束位置，找不到時回傳 -1"""
    start_char = text[0]
    end_char = '>' if start_char == '<' else ']'
    depth = 0
    for i, c in enumerate(text):
        if c == start_char:
            depth += 1
        elif c == end_char:
            depth -= 1
            if depth == 0:
                return i
    return -1


def new_result(text: str) -> Dict[str, Any]:
    return {
        'text': text,
        'cont': False,
        'is_subtitle': False,
        'is_important': False,
        'indent': 0,
        'align': None,
        'link': None,
        'image': None,
        'styles': {},
    }


def apply_format(fmt: str, tokens: List[str], result: Dict[str, Any]) -> None:
    """應用單個格式標記到結果"""
    if 'cont' in tokens:
        result['cont'] = True

    if 'ct' in tokens:
        result['is_subtitle'] = True

    if 'imp' in tokens:
        result['is_important'] = True

    tab_match = re.search(r'tab<(\d+)>', fmt)
    if tab_match:
        result['indent'] = int(tab_match.group(1))

    pivot_match = re.search(r'pivot<([lcr])>', fmt)
    if pivot_match:
        result['align'] = PIVOT_MAP.get(pivot_match.group(1))

    link_match = re.search(r'link<([^>]+)>', fmt)
    if link_match:
        result['link'] = link_match.group(1)

    img_match = re.search(r'img<([^,]+),([^,]+),([^>]+)>', fmt)
    if img_match:
        result['image'] = {
            'url': img_match.group(1),
            'width': img_match.group(2),
            'height': img_match.group(3),
        }

    size_match = re.search(r'size<(\d)>', fmt)
    if size_match and size_match.group(1) in SIZE_MAP:
        result['styles']['font-size'] = SIZE_MAP[size_match.group(1)]

    color_match = re.search(r'color<([^>]+)>', fmt)
    if color_match:
        result['styles']['color'] = normalize_color(color_match.group(1))

    if 'b' in tokens or 'bold' in tokens:
        result['styles']['font-weight'] = 'bold'

    if 'i' in tokens or 'italic' in tokens:
        result['styles']['font-style'] = 'italic'

    underline = 'u' in tokens or 'underline' in tokens
    strike = 's' in tokens or 'strike' in tokens

    if underline and strike:
        result['styles']['text-decoration'] = 'underline line-through'
    elif underline:
        result['styles']['text-decoration'] = 'underline'
    elif strike:
        result['styles']['text-decoration'] = 'line-through'


def parse_tags(
    text: str,
    *,
    openers: str,
    multi: bool,
    strip: bool,
    tokenize: Callable[[str], List[str]],
) -> Dict[str, Any]:
    """
    解析開頭的格式標記

    openers: 可作為標記開頭的字元
    multi: 是否連續解析多個標記
    strip: 標記後的剩餘文字是否 strip（未解析到標記時也回傳 strip 後的文字）
    tokenize: 切割標記內容的方式
    """
    result = new_result(text)

    stripped = text.strip()
    if not stripped:
        return result

    rest = stripped
    consumed = False
    while rest and rest[0] in openers:
        end = find_tag_end(rest)
        if end == -1:
            break

        fmt = rest[1:end]
        rest = rest[end+1:]
        if strip:
            rest = rest.strip()
        apply_format(fmt, tokenize(fmt), result)
        consumed = True

        if not multi:
            break

    if consumed or strip:
        result['text'] = rest
    return result


def parse_line_format(line: str) -> Dict[str, Any]:
    """解析行內文字的格式標記"""
    return parse_tags(line, openers='<[', multi=True, strip=True,
                      tokenize=split_tokens_regex)


def parse_cell_format(text: str) -> Dict[str, Any]:
    """解析表格儲存格與樹節點文字的格式標記"""
    parsed = parse_tags(text, openers='<', multi=False, strip=False,
                        tokenize=split_tokens_whitespace)
    return {
        'text': parsed['text'],
        'imp': parsed['is_important'],
        'styles': parsed['styles'],
    }
