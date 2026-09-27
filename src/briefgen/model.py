#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
model.py - 投影片數據模型
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Slide:
    """單張投影片"""
    title: str = ""
    subtitle: str = ""
    content: str = ""  # Markdown 格式內容
    # 每個內容行在來源 Markdown 檔中的行號（僅供警告使用）
    source_lines: Optional[List[int]] = field(default=None, repr=False, compare=False)


@dataclass
class Presentation:
    """簡報"""
    title: str = "簡報"
    slides: List[Slide] = field(default_factory=list)
