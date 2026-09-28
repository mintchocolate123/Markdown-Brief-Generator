#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動器入口：確認已安裝 briefgen 後開啟中文選單（主程式在 src/briefgen/launcher.py）

把 .md 檔拖到 start.bat 上時，檔案路徑會當成參數傳進來，直接開始即時預覽。
"""

import importlib.util
import sys
from pathlib import Path


def use_utf8_output():
    """stdout/stderr 改用 UTF-8，不依賴系統編碼（未安裝 briefgen 時也要能執行）；
    輸入無法解碼的字元以替代字元處理，不讓啟動器當掉"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(errors='replace')


def main():
    use_utf8_output()
    if importlib.util.find_spec('briefgen') is None:
        print("找不到 briefgen 套件，請先在工具目錄執行一次：")
        print()
        print("    pip install -e .")
        try:
            input("\n按 Enter 結束...")
        except EOFError:
            pass
        return
    from briefgen.launcher import main as run
    run(Path(__file__).resolve().parent, sys.argv[1:])


if __name__ == '__main__':
    main()
