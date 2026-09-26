#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slides.py - 將 Markdown 檔案切割為投影片
"""

from briefgen.model import Slide


def _count_leading_newlines(text: str) -> int:
    """strip() 會移除的開頭行數"""
    return text[:len(text) - len(text.lstrip())].count('\n')


def parse_markdown_slides(content: str) -> list[Slide]:
    """解析 Markdown 檔案內容"""
    slides = []

    # 分割投影片（以 --- 或 # 開頭的標題為分隔）
    parts = content.split('\n---\n')

    part_start = 1  # 目前這一段在檔案中的起始行號
    for raw_part in parts:
        next_start = part_start + raw_part.count('\n') + 2

        part = raw_part.strip()
        if not part:
            part_start = next_start
            continue

        first_line = part_start + _count_leading_newlines(raw_part)
        lines = part.split('\n')
        title = ""
        subtitle = ""
        content_lines = []
        content_line_numbers = []

        # 解析標題和內容
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 主標題 (# 開頭)
            if line.startswith('# '):
                title = line[2:].strip()
                i += 1
                continue

            # 副標題 (## 開頭)
            if line.startswith('## '):
                subtitle = line[3:].strip()
                i += 1
                continue

            # 其他內容
            content_lines.append(lines[i])
            content_line_numbers.append(first_line + i)
            i += 1

        joined = '\n'.join(content_lines)
        slide_content = joined.strip()
        skipped = _count_leading_newlines(joined)

        slide = Slide(
            title=title,
            subtitle=subtitle,
            content=slide_content,
            source_lines=content_line_numbers[skipped:skipped + slide_content.count('\n') + 1],
        )
        slides.append(slide)
        part_start = next_start

    return slides
