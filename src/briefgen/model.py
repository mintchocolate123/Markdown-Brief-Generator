#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
model.py - 投影片數據模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SlideTheme:
    """投影片主題配色"""
    primary_color: str = "#e94560"
    secondary_color: str = "#ff6b6b"
    accent_color: str = "#feca57"
    bg_start: str = "#1a1a2e"
    bg_mid: str = "#16213e"
    bg_end: str = "#0f3460"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'bg_start': self.bg_start,
            'bg_mid': self.bg_mid,
            'bg_end': self.bg_end,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'SlideTheme':
        return cls(**data)


@dataclass
class Slide:
    """單張投影片"""
    title: str = ""
    subtitle: str = ""
    content: str = ""  # Markdown 格式內容
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'subtitle': self.subtitle,
            'content': self.content,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Slide':
        return cls(
            title=data.get('title', ''),
            subtitle=data.get('subtitle', ''),
            content=data.get('content', ''),
            metadata=data.get('metadata', {}),
        )
    
    def get_display_name(self) -> str:
        """取得顯示名稱"""
        if self.title.strip() and self.subtitle.strip():
            return f"{self.title} - {self.subtitle}"
        return self.title.strip() or "(無標題)"


@dataclass
class Presentation:
    """簡報專案"""
    title: str = "簡報"
    slides: List[Slide] = field(default_factory=list)
    theme: SlideTheme = field(default_factory=SlideTheme)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'slides': [slide.to_dict() for slide in self.slides],
            'theme': self.theme.to_dict(),
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Presentation':
        return cls(
            title=data.get('title', '簡報'),
            slides=[Slide.from_dict(s) for s in data.get('slides', [])],
            theme=SlideTheme.from_dict(data.get('theme', {})),
            metadata=data.get('metadata', {}),
        )
    
    def add_slide(self, slide: Slide) -> None:
        """新增投影片"""
        self.slides.append(slide)
    
    def remove_slide(self, index: int) -> None:
        """移除投影片"""
        if 0 <= index < len(self.slides):
            del self.slides[index]
    
    def move_slide(self, from_index: int, to_index: int) -> None:
        """移動投影片"""
        if 0 <= from_index < len(self.slides) and 0 <= to_index < len(self.slides):
            slide = self.slides.pop(from_index)
            self.slides.insert(to_index, slide)
