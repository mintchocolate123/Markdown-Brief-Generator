#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動器 - 支援路徑切換的中文互動式介面
"""

import importlib.util
import os
import sys
import subprocess
from pathlib import Path


def clear_screen():
    """清除螢幕"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_absolute_path(path_str):
    """取得絕對路徑"""
    path = Path(path_str).expanduser()
    if path.is_absolute():
        return path
    else:
        return Path.cwd() / path


def run_generator(*args):
    """以 python -m briefgen 執行生成器"""
    try:
        result = subprocess.run([sys.executable, '-m', 'briefgen', *args], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


def open_file(filepath):
    """開啟檔案"""
    path = get_absolute_path(filepath)
    if os.name == 'nt':
        os.startfile(str(path))
    else:
        subprocess.run(['open', str(path)])


def build_from_markdown():
    """從 Markdown 生成簡報"""
    clear_screen()
    print("=" * 50)
    print("    從 Markdown 生成簡報")
    print("=" * 50)
    print()
    print("提示：可以使用完整路徑或相對路徑")
    print("範例：")
    print("  - 當前目錄：example.md")
    print("  - 上層目錄：../slides/my_slides.md")
    print("  - 完整路徑：C:\\Users\\Name\\slides.md")
    print()
    
    input_file = input("請輸入 Markdown 檔案路徑: ").strip().strip('"')
    if not input_file:
        print("錯誤：檔案名稱不能為空")
        input("\n按 Enter 繼續...")
        return
    
    input_path = get_absolute_path(input_file)
    if not input_path.exists():
        print(f"錯誤：找不到檔案")
        print(f"尋找路徑：{input_path}")
        input("\n按 Enter 繼續...")
        return
    
    # 預設輸出與輸入同目錄
    default_output = input_path.parent / f"{input_path.stem}_output.html"
    
    output_file = input(f"輸出檔案 [預設: {default_output.name}]: ").strip().strip('"')
    if not output_file:
        output_path = default_output
    else:
        output_path = get_absolute_path(output_file)
    
    print(f"\n生成中...")
    print(f"來源：{input_path}")
    print(f"輸出：{output_path}\n")
    
    if run_generator('build', '-i', str(input_path), '-o', str(output_path)):
        print("\n[OK] 完成！")
        if input("\n開啟簡報？(y/n): ").strip().lower() == 'y':
            open_file(output_path)
    else:
        print("\n[FAIL] 失敗")
    
    input("\n按 Enter 繼續...")


def generate_example():
    """生成範例"""
    clear_screen()
    print("=" * 50)
    print("    生成範例簡報")
    print("=" * 50)
    print()
    
    script_dir = Path(__file__).parent
    example = script_dir / 'examples' / 'example.md'
    output = Path.cwd() / 'example_output.html'
    
    if not example.exists():
        print("找不到 examples/example.md")
        input("\n按 Enter 繼續...")
        return
    
    print(f"輸出：{output}\n")
    
    if run_generator('build', '-i', str(example), '-o', str(output), '--title', '範例'):
        print("\n[OK] 完成！")
        if input("\n開啟？(y/n): ").strip().lower() == 'y':
            open_file(output)
    else:
        print("\n[FAIL] 失敗")
    
    input("\n按 Enter 繼續...")


def use_utf8_output():
    """stdout/stderr 改用 UTF-8，不依賴系統編碼（未安裝 briefgen 時也要能執行）"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')


def main():
    """主選單"""
    use_utf8_output()
    
    if importlib.util.find_spec('briefgen') is None:
        print("找不到 briefgen 套件，請先在工具目錄執行一次：")
        print()
        print("    pip install -e .")
        input("\n按 Enter 結束...")
        return
    
    from briefgen import __version__
    
    while True:
        clear_screen()
        print("=" * 50)
        print(f"    HTML 簡報生成器 v{__version__}")
        print("=" * 50)
        print(f"\n當前目錄: {Path.cwd()}\n")
        print("[1] 從 Markdown 生成簡報")
        print("[2] 生成範例")
        print("[0] 結束")
        print()
        
        choice = input("選擇 (0-2): ").strip()
        
        if choice == '1':
            build_from_markdown()
        elif choice == '2':
            generate_example()
        elif choice == '0':
            clear_screen()
            print("\n謝謝使用！\n")
            break


if __name__ == '__main__':
    main()
