#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_syntax.py - 將舊版格式語法轉換為新語法

    <size<5>><b>文字      ->  <size=5 b>文字
    [width<400px>]        ->  [width=400px]
    [id<2> p<1> o<1/2>]   ->  [id=2 p=1]

用法：
    python tools/migrate_syntax.py 舊檔.md -o 新檔.md
    python tools/migrate_syntax.py 舊檔.md --in-place

舊版會忽略、新語法又不接受的內容會被移除，並列在轉換報告（stderr）中。
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from briefgen.parsing.slides import split_slide_ranges
except ImportError:  # 尚未 pip install 時，從原始碼目錄載入
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
    from briefgen.parsing.slides import split_slide_ranges


FLAG_NAMES = {'b', 'bold', 'i', 'italic', 'u', 'underline', 's', 'strike', 'ct', 'imp', 'cont'}

# 舊版角括號參數的有效寫法（與舊版解析的正規表示式一致），img 另外要求剛好三個欄位
ARG_PATTERNS = {
    'tab': r'\d+',
    'pivot': r'[lcr]',
    'size': r'[1-7]',
    'color': r'[^>]+',
    'link': r'[^>]+',
    'img': r'[^,>]+,[^,>]+,[^,>]+',
}

TREE_ARG_NAMES = {'id', 'p'}
TREE_REMOVED_NAMES = {'o', 'imp'}

OLD_ITEM_RE = re.compile(r'^(\w+)<(.*)>$')
NEW_ITEM_RE = re.compile(r'^(\w+)=(.*)$')
WIDTH_RE = re.compile(r'^(\s*)\[width<([^>]+)>\](.*)$')
NEW_WIDTH_RE = re.compile(r'^\s*\[width=[^\]]+\]')


class Report:
    def __init__(self):
        self.lines: List[str] = []
        self.line_no = 0

    def add(self, message: str) -> None:
        self.lines.append(f'第 {self.line_no} 行: {message}')


def find_tag_end(text: str) -> int:
    """找到開頭標記對應的結束位置（與舊版相同的深度比對），找不到時回傳 -1"""
    start_char = text[0]
    end_char = '>' if start_char == '<' else ']'
    depth = 0
    in_quote = False
    for i, c in enumerate(text):
        if c == '"':
            in_quote = not in_quote
        elif in_quote:
            continue
        elif c == start_char:
            depth += 1
        elif c == end_char:
            depth -= 1
            if depth == 0:
                return i
    return -1


def split_items(fmt: str) -> List[str]:
    """以頂層空白切割標記內容（角括號與雙引號內不切）"""
    items = []
    current = ''
    depth = 0
    in_quote = False
    for c in fmt:
        if c == '"':
            in_quote = not in_quote
        elif not in_quote:
            if c == '<':
                depth += 1
            elif c == '>':
                depth -= 1
            elif c.isspace() and depth == 0:
                if current:
                    items.append(current)
                current = ''
                continue
        current += c
    if current:
        items.append(current)
    return items


def quote_value(value: str) -> Optional[str]:
    """需要時為值加上雙引號；無法表示時回傳 None"""
    if not re.search(r'[\s>"]', value):
        return value
    if '"' in value:
        return None
    return f'"{value}"'


def convert_format_item(item: str) -> Optional[str]:
    """轉換行首格式的單一項目；舊版沒有作用的項目回傳 None"""
    new = NEW_ITEM_RE.match(item)
    if new and new.group(1) in ARG_PATTERNS:
        return item
    if item in FLAG_NAMES:
        return item
    match = OLD_ITEM_RE.match(item)
    if not match:
        return None
    name, arg = match.groups()
    pattern = ARG_PATTERNS.get(name)
    if pattern is None or not re.fullmatch(pattern, arg):
        return None
    quoted = quote_value(arg)
    return f'{name}={quoted}' if quoted else None


def convert_fmt(fmt: str, report: Report) -> List[str]:
    """轉換一個標記的內容為新語法項目，並回報被移除的項目"""
    items = split_items(fmt)
    if not items:
        report.add('移除空的 <>')
        return []
    converted = []
    for item in items:
        new_item = convert_format_item(item)
        if new_item is None:
            report.add(f'移除舊版沒有作用的格式 {item}')
        else:
            converted.append(new_item)
    return converted


def is_known_bracket(fmt: str) -> bool:
    """段落行首的 [...] 是否全由有效格式組成"""
    items = split_items(fmt)
    return bool(items) and all(convert_format_item(item) is not None for item in items)


def convert_leading_tags(text: str, report: Report, allow_square: bool) -> str:
    """把行首連續的舊版標記合併為一個新語法標記"""
    indent = text[:len(text) - len(text.lstrip())]
    rest = text.lstrip()
    tokens: List[str] = []
    consumed = False

    openers = ('<', '[') if allow_square else ('<',)
    while rest and rest[0] in openers:
        end = find_tag_end(rest)
        if end == -1:
            break
        fmt = rest[1:end]
        if rest[0] == '[' and not is_known_bracket(fmt):
            report.add(f'段落行首的 [{fmt}] 在新語法中會顯示為文字（舊版會被隱藏）')
            break
        tokens.extend(convert_fmt(fmt, report))
        consumed = True
        rest = rest[end+1:]
        # 舊版在標記之間會 strip；最後一個標記後的空白保留給 cont 使用
        if rest.lstrip()[:1] in openers:
            rest = rest.lstrip()

    if not consumed:
        return text
    if not tokens:
        return indent + rest.lstrip()
    return f'{indent}<{" ".join(tokens)}>{rest}'


def convert_width(line: str) -> Optional[str]:
    """轉換寬度設定行；已是新語法時原樣回傳，不是寬度設定時回傳 None"""
    if NEW_WIDTH_RE.match(line):
        return line
    match = WIDTH_RE.match(line)
    if not match:
        return None
    indent, value, rest = match.groups()
    return f'{indent}[width={quote_value(value) or value}]{rest}'


def convert_tree_node(line: str, report: Report) -> str:
    indent = line[:len(line) - len(line.lstrip())]
    stripped = line.lstrip()
    if not stripped.startswith('['):
        return line
    end = find_tag_end(stripped)
    if end == -1:
        return line

    tokens = []
    for item in split_items(stripped[1:end]):
        old = OLD_ITEM_RE.match(item)
        new = NEW_ITEM_RE.match(item)
        name = (old or new).group(1) if (old or new) else item
        if old and name in TREE_ARG_NAMES:
            tokens.append(f'{name}={quote_value(old.group(2)) or old.group(2)}')
        elif new and name in TREE_ARG_NAMES:
            tokens.append(item)
        elif name in TREE_REMOVED_NAMES:
            report.add(f'移除樹節點的 {item}')
        else:
            report.add(f'移除樹節點沒有作用的 {item}')

    after = stripped[end+1:]
    space = after[:len(after) - len(after.lstrip())]
    text = convert_leading_tags(after.lstrip(), report, allow_square=False)
    return f'{indent}[{" ".join(tokens)}]{space}{text}'


def convert_cell(line: str, report: Report) -> str:
    stripped = line.lstrip()
    if stripped.startswith('[c]'):
        prefix_len = len(line) - len(stripped) + 3
        return line[:prefix_len] + convert_leading_tags(line[prefix_len:], report, allow_square=False)
    return convert_leading_tags(line, report, allow_square=False)


def find_block_end(lines: List[str], start: int, closer: str) -> int:
    for i in range(start + 1, len(lines)):
        if lines[i].strip() == closer:
            return i
    return -1


def is_heading(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith('# ') or stripped.startswith('## ')


BLOCKS = {
    '[table]': ('[/table]', convert_cell),
    '[tree]': ('[/tree]', convert_tree_node),
}

CODE_BLOCK = ('```', lambda line, report: line)


def migrate_slide(lines: List[str], offset: int, report: Report) -> List[str]:
    """轉換一張投影片的行（舊版的區塊不會跨越投影片，標題行不屬於內容）"""
    out = list(lines)
    i = 0
    while i < len(lines):
        report.line_no = offset + i + 1
        line = lines[i]
        if is_heading(line):
            i += 1
            continue

        stripped = line.strip()
        block = CODE_BLOCK if stripped.startswith('```') else BLOCKS.get(stripped)
        end = find_block_end(lines, i, block[0]) if block else -1
        if end == -1:
            out[i] = convert_leading_tags(line, report, allow_square=True)
            i += 1
            continue

        convert = block[1]
        for j in range(i + 1, end):
            report.line_no = offset + j + 1
            if not is_heading(lines[j]):
                out[j] = convert_width(lines[j]) or convert(lines[j], report)
        i = end + 1

    return out


def migrate(text: str) -> Tuple[str, List[str]]:
    """轉換整份 Markdown，回傳新內容與轉換報告"""
    lines = text.split('\n')
    report = Report()

    # 與生成器相同的分頁方式（程式碼區塊內的 --- 不分頁），分隔線原樣保留
    out: List[str] = []
    for k, (start, stop) in enumerate(split_slide_ranges(lines)):
        if k > 0:
            out.append(lines[start - 1])
        out.extend(migrate_slide(lines[start:stop], start, report))

    return '\n'.join(out), report.lines


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='將舊版格式語法轉換為新語法')
    parser.add_argument('input', help='舊語法的 Markdown 檔案')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-o', '--output', help='輸出檔案')
    group.add_argument('--in-place', action='store_true', help='直接覆寫輸入檔案')
    args = parser.parse_args(argv)

    source = Path(args.input)
    text, report = migrate(source.read_text(encoding='utf-8'))

    target = source if args.in_place else Path(args.output)
    target.write_text(text, encoding='utf-8')

    for line in report:
        print(f'{source}: {line}', file=sys.stderr)
    print(f'已轉換: {target}（報告 {len(report)} 項）', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
