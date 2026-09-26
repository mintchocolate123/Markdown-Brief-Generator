#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slides.py - 將 Markdown 檔案切割為投影片

以單獨一行的 --- 分頁，# / ## 開頭的行是標題與副標題。
``` 程式碼區塊內的任何內容都不影響分頁與標題。
"""

from briefgen.model import Slide


def find_fence_lines(lines: list[str]) -> set[int]:
    """回傳位於 ``` 程式碼區塊內（含開頭與結尾）的行索引；沒有結尾的 ``` 不算區塊"""
    fenced = set()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('```'):
            end = next((j for j in range(i + 1, len(lines)) if lines[j].strip() == '```'), -1)
            if end != -1:
                fenced.update(range(i, end + 1))
                i = end + 1
                continue
        i += 1
    return fenced


def split_slide_ranges(lines: list[str]) -> list[tuple[int, int]]:
    """回傳每張投影片的行範圍 [start, stop)，不含分隔線"""
    fenced = find_fence_lines(lines)
    ranges = []
    start = 0
    for i, line in enumerate(lines):
        # 分隔線不能是第一行或最後一行，與 '\n---\n' 的切法一致
        if line == '---' and 0 < i < len(lines) - 1 and i not in fenced:
            ranges.append((start, i))
            start = i + 1
    ranges.append((start, len(lines)))
    return ranges


def _is_heading(line: str, prefix: str) -> bool:
    return line.strip().startswith(prefix)


def parse_markdown_slides(content: str) -> list[Slide]:
    """解析 Markdown 檔案內容"""
    slides = []
    lines = content.split('\n')
    fenced = find_fence_lines(lines)

    for start, stop in split_slide_ranges(lines):
        if not '\n'.join(lines[start:stop]).strip():
            continue

        title = ""
        subtitle = ""
        content_lines = []
        content_line_numbers = []

        for i in range(start, stop):
            line = lines[i]

            if i not in fenced:
                # 主標題 (# 開頭)
                if _is_heading(line, '# '):
                    title = line.strip()[2:].strip()
                    continue

                # 副標題 (## 開頭)
                if _is_heading(line, '## '):
                    subtitle = line.strip()[3:].strip()
                    continue

            # 其他內容
            content_lines.append(line)
            content_line_numbers.append(i + 1)

        joined = '\n'.join(content_lines)
        slide_content = joined.strip()
        skipped = joined[:len(joined) - len(joined.lstrip())].count('\n')

        slides.append(Slide(
            title=title,
            subtitle=subtitle,
            content=slide_content,
            source_lines=content_line_numbers[skipped:skipped + slide_content.count('\n') + 1],
        ))

    return slides
