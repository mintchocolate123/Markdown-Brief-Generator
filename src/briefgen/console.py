#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
console.py - 終端輸出設定
"""

import sys


def use_utf8_output() -> None:
    """stdout/stderr 改用 UTF-8（無法編碼的字元以 ? 取代），不依賴系統編碼"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
