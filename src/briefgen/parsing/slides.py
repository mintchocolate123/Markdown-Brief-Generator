#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slides.py - 將 Markdown 檔案切割為投影片
"""

from briefgen.model import Slide


def parse_markdown_slides(content: str) -> list[Slide]:
    """解析 Markdown 檔案內容"""
    slides = []
    
    # 分割投影片（以 --- 或 # 開頭的標題為分隔）
    parts = content.split('\n---\n')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        lines = part.split('\n')
        title = ""
        subtitle = ""
        content_lines = []
        
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
            i += 1
        
        slide = Slide(
            title=title,
            subtitle=subtitle,
            content='\n'.join(content_lines).strip()
        )
        slides.append(slide)
    
    return slides
