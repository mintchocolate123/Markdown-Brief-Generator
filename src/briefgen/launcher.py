#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
launcher.py - 中文選單啟動器

簡報放在「文件」資料夾底下的 brief，每份簡報一個子資料夾：
    brief/<名稱>/<名稱>.md、<名稱>.html、images/
輸出一律存在 .md 旁邊，檔名和 .md 相同。

測試用的環境變數：BRIEFGEN_HOME（取代家目錄）、BRIEFGEN_DOCUMENTS（取代「文件」資料夾）、
BRIEFGEN_NO_GUI=1（不開啟 tkinter 視窗，改用手動輸入）。
"""

import json
import os
import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import List, Optional

from briefgen import __version__

RECENT_LIMIT = 5
CHEATSHEET_URL = 'https://github.com/mintchocolate123/Markdown-Brief-Generator/blob/main/docs/語法速查.md'
INVALID_NAME_CHARS = '\\/:*?"<>|'
RESERVED_NAMES = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}


class GuiUnavailable(Exception):
    """無法開啟 tkinter 視窗"""


# --- 路徑 --------------------------------------------------------------------

def home_dir() -> Path:
    return Path(os.environ.get('BRIEFGEN_HOME') or Path.home())


def _windows_documents() -> Optional[Path]:
    """以 SHGetKnownFolderPath 取得「文件」的實際位置（OneDrive 或使用者搬移過也正確）"""
    import ctypes
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [('Data1', wintypes.DWORD), ('Data2', wintypes.WORD),
                    ('Data3', wintypes.WORD), ('Data4', ctypes.c_ubyte * 8)]

    folder_id = GUID(0xFDD39AD0, 0x238F, 0x46AF,
                     (ctypes.c_ubyte * 8)(0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7))
    path = ctypes.c_wchar_p()
    result = ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(folder_id), 0, None, ctypes.byref(path))
    try:
        return Path(path.value) if result == 0 and path.value else None
    finally:
        ctypes.windll.ole32.CoTaskMemFree(path)


def _xdg_documents(home: Path) -> Optional[Path]:
    """讀取 XDG 設定（~/.config/user-dirs.dirs）中的 XDG_DOCUMENTS_DIR"""
    config_home = Path(os.environ.get('XDG_CONFIG_HOME') or home / '.config')
    try:
        text = (config_home / 'user-dirs.dirs').read_text(encoding='utf-8')
    except OSError:
        return None
    match = re.search(r'^XDG_DOCUMENTS_DIR="([^"]+)"', text, re.M)
    if not match:
        return None
    path = Path(match.group(1).replace('$HOME', str(home)))
    return path if path != home else None


def documents_dir() -> Path:
    """使用者的「文件」資料夾"""
    if os.environ.get('BRIEFGEN_DOCUMENTS'):
        return Path(os.environ['BRIEFGEN_DOCUMENTS'])
    home = home_dir()
    found = None
    if os.name == 'nt':
        try:
            found = _windows_documents()
        except (OSError, AttributeError):
            found = None
    elif sys.platform.startswith('linux'):
        found = _xdg_documents(home)
    return found or home / 'Documents'


def config_path() -> Path:
    return home_dir() / '.briefgen' / 'launcher.json'


# --- 設定與最近使用 ------------------------------------------------------------

def load_config() -> dict:
    try:
        data = json.loads(config_path().read_text(encoding='utf-8'))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault('brief_dir', '')
    data.setdefault('recent', [])
    return data


def save_config(config: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')


def brief_dir(config: dict) -> Path:
    return Path(config['brief_dir']) if config.get('brief_dir') else documents_dir() / 'brief'


def ensure_brief_dir(config: dict) -> bool:
    """簡報資料夾不存在就建立，回傳是否新建"""
    folder = brief_dir(config)
    if folder.is_dir():
        return False
    folder.mkdir(parents=True, exist_ok=True)
    return True


def recent_files(config: dict) -> List[Path]:
    """最近使用的簡報；已經不存在的檔案自動移除"""
    existing = [p for p in config['recent'] if Path(p).is_file()]
    if existing != config['recent']:
        config['recent'] = existing
        save_config(config)
    return [Path(p) for p in existing]


def add_recent(config: dict, path: Path) -> None:
    path = str(Path(path).resolve())
    config['recent'] = [path] + [p for p in config['recent'] if p != path][:RECENT_LIMIT - 1]
    save_config(config)


def clear_recent(config: dict) -> None:
    config['recent'] = []
    save_config(config)


# --- 檔名與備份 ----------------------------------------------------------------

def name_error(name: str) -> Optional[str]:
    """簡報名稱不合法時回傳原因（所有系統都用 Windows 的規則）"""
    if any(c in INVALID_NAME_CHARS for c in name) or any(ord(c) < 32 for c in name):
        return f'名稱不能包含 {" ".join(INVALID_NAME_CHARS)} 這些字元，請重新輸入。'
    if name.endswith(('.', ' ')):
        return '名稱的結尾不能是句點或空白，請重新輸入。'
    if name.split('.')[0].upper() in RESERVED_NAMES:
        return f'「{name}」是系統保留的名稱，請換一個名稱。'
    return None


def backup_path(md: Path) -> Path:
    """<名稱>.v2.bak.md；已存在時改用 <名稱>.v2.bak-2.md、-3…，不覆蓋舊備份"""
    candidate = md.with_name(f'{md.stem}.v2.bak.md')
    number = 2
    while candidate.exists():
        candidate = md.with_name(f'{md.stem}.v2.bak-{number}.md')
        number += 1
    return candidate


# --- 外部程式 ------------------------------------------------------------------

def run_briefgen(*args: str) -> bool:
    return subprocess.run([sys.executable, '-m', 'briefgen', *args]).returncode == 0


def build(md: Path, output: Optional[Path] = None) -> Optional[Path]:
    """生成 HTML（預設存在 .md 旁邊、同檔名），成功時回傳 HTML 路徑"""
    output = output or md.with_suffix('.html')
    print(f'\n生成中：{md}', flush=True)
    if not run_briefgen('build', '-i', str(md), '-o', str(output)):
        print('[FAIL] 生成失敗，請看上面的訊息')
        return None
    print(f'[OK] 已生成：{output}')
    return output


def open_in_browser(path: Path) -> None:
    webbrowser.open(path.resolve().as_uri())


def open_folder(path: Path) -> None:
    if os.name == 'nt':
        os.startfile(str(path))
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', str(path)])
    else:
        subprocess.Popen(['xdg-open', str(path)])


def open_in_text_editor(path: Path) -> None:
    if os.name == 'nt':
        subprocess.Popen(['notepad', str(path)])
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', '-t', str(path)])
    else:
        subprocess.Popen(['xdg-open', str(path)])


def pick_file_dialog(initial_dir: Path) -> Optional[Path]:
    """tkinter 開檔視窗（只顯示 .md）；取消時回傳 None，無法開視窗時丟出 GuiUnavailable"""
    if os.environ.get('BRIEFGEN_NO_GUI') == '1':
        raise GuiUnavailable()
    try:
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk()
    except Exception as error:  # 沒有 tkinter、沒有顯示器等
        raise GuiUnavailable() from error
    try:
        root.withdraw()
        root.attributes('-topmost', True)
        chosen = filedialog.askopenfilename(
            parent=root, initialdir=str(initial_dir), title='選擇簡報',
            filetypes=[('Markdown 簡報', '*.md')])
    finally:
        root.destroy()
    return Path(chosen) if chosen else None


def pick_folder_dialog(initial_dir: Path) -> Optional[Path]:
    if os.environ.get('BRIEFGEN_NO_GUI') == '1':
        raise GuiUnavailable()
    try:
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk()
    except Exception as error:
        raise GuiUnavailable() from error
    try:
        root.withdraw()
        root.attributes('-topmost', True)
        chosen = filedialog.askdirectory(parent=root, initialdir=str(initial_dir), title='選擇簡報資料夾')
    finally:
        root.destroy()
    return Path(chosen) if chosen else None


def gui_available() -> bool:
    if os.environ.get('BRIEFGEN_NO_GUI') == '1':
        return False
    try:
        import tkinter  # noqa: F401
    except ImportError:
        return False
    return True


# --- 畫面 ----------------------------------------------------------------------

def clear_screen() -> None:
    if sys.stdout.isatty():
        os.system('cls' if os.name == 'nt' else 'clear')


def header(title: str) -> None:
    clear_screen()
    print('=' * 50)
    print(f'    {title}')
    print('=' * 50)


def ask(prompt: str) -> str:
    return input(prompt).strip()


def pause() -> None:
    input('\n按 Enter 繼續...')


def clean_path(text: str) -> str:
    """去掉拖進視窗時加上的引號"""
    return text.strip().strip('"').strip("'").strip()


# --- 選檔 ----------------------------------------------------------------------

def check_markdown(path: Path) -> Optional[str]:
    if path.suffix.lower() != '.md':
        return f'只能選擇 .md 檔：{path}'
    if not path.is_file():
        return f'找不到檔案：{path}'
    return None


def choose_markdown(config: dict, title: str) -> Optional[Path]:
    """從最近使用或開檔視窗選擇 .md；回上一層時回傳 None"""
    while True:
        header(title)
        recent = recent_files(config)
        if recent:
            print('最近使用：')
            for number, path in enumerate(recent, 1):
                print(f' [{number}] {path.stem}    {path}')
        else:
            print('（還沒有最近使用的簡報）')
        print()
        if gui_available():
            print(' [F] 用開檔視窗選擇')
        else:
            print(' [F] 手動輸入路徑（可以把 .md 檔拖進這個視窗）')
        print(' [0] 回上一層（直接按 Enter 也可以）')
        print()
        choice = ask('請選擇：')
        if choice in ('', '0'):
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(recent):
            return recent[int(choice) - 1]
        if choice.upper() == 'F':
            path = _pick_or_type(brief_dir(config))
            if path is None:
                continue
            error = check_markdown(path)
            if error:
                print(f'[FAIL] {error}')
                pause()
                continue
            return path
        print('請輸入選單上的編號。')
        pause()


def _pick_or_type(initial_dir: Path) -> Optional[Path]:
    try:
        return pick_file_dialog(initial_dir)
    except GuiUnavailable:
        text = clean_path(ask('請輸入 .md 路徑（可以把檔案拖進這個視窗，直接按 Enter 取消）：'))
        return Path(text).expanduser() if text else None


# --- 功能 ----------------------------------------------------------------------

def after_build(html: Path) -> None:
    print()
    print(' [1] 開啟簡報')
    print(' [2] 開啟所在資料夾')
    print(' [0] 回選單（直接按 Enter 也可以）')
    choice = ask('請選擇：')
    if choice == '1':
        open_in_browser(html)
    elif choice == '2':
        open_folder(html.parent)


def build_deck(config: dict, md: Optional[Path] = None) -> None:
    md = md or choose_markdown(config, '開啟 / 生成簡報')
    if md is None:
        return
    html = build(md)
    add_recent(config, md)
    if html:
        after_build(html)
    else:
        pause()


def preview(config: dict, md: Optional[Path] = None) -> None:
    md = md or choose_markdown(config, '即時預覽')
    if md is None:
        return
    add_recent(config, md)
    print(f'\n即時預覽：{md}', flush=True)
    process = subprocess.Popen([sys.executable, '-m', 'briefgen', 'watch', str(md)])
    try:
        process.wait()
    except KeyboardInterrupt:
        # Ctrl+C 同時送給 watch，等它自己結束
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
    print('\n已結束即時預覽，回到選單')
    pause()


def new_deck(config: dict, repo: Path) -> None:
    header('新增簡報')
    print(f'簡報會建立在：{brief_dir(config)}\n')
    while True:
        name = ask('請輸入簡報名稱（直接按 Enter 回上一層）：')
        if not name or name == '0':
            return
        error = name_error(name)
        if error:
            print(error)
            continue
        folder = brief_dir(config) / name
        if folder.exists():
            print('已經有同名的簡報資料夾，請換一個名稱。')
            continue
        break
    folder.mkdir(parents=True)
    md = folder / f'{name}.md'
    shutil.copyfile(repo / 'examples' / 'template.md', md)
    (folder / 'images').mkdir()
    add_recent(config, md)
    print(f'[OK] 已建立：{folder}{os.sep}')
    print(f'       {md.name}')
    print(f'       images{os.sep}')
    if ask('要直接開始即時預覽嗎？(y/n)：').lower() == 'y':
        preview(config, md)


def migrate(config: dict, repo: Path) -> None:
    md = choose_markdown(config, '轉換舊簡報')
    if md is None:
        return
    backup = backup_path(md)
    shutil.copy2(md, backup)
    print(f'\n已備份：{backup}')
    result = subprocess.run(
        [sys.executable, str(repo / 'tools' / 'migrate_syntax.py'), str(md), '--in-place'],
        capture_output=True, encoding='utf-8', errors='replace')
    report = [m.group(1) for m in re.finditer(r'(第 \d+ 行: .*)$', result.stderr, re.M)]
    if report:
        print('轉換報告：')
        for line in report:
            print(f'  {line}')
    else:
        print('轉換報告：沒有需要留意的內容')
    inline = sum('行中間的' in line for line in report)
    if inline:
        print(f'[注意] 有 {inline} 行在行中間寫了舊標籤，這些格式不會套用，'
              '請手動拆成 cont 行（見使用指南）。')
    if result.returncode != 0:
        print('[FAIL] 轉換失敗，原檔已保留在備份')
        pause()
        return
    add_recent(config, md)
    print(f'[OK] 轉換完成：{md}')
    print()
    print(' [1] 開始即時預覽')
    print(' [2] 生成簡報')
    print(' [0] 回選單（直接按 Enter 也可以）')
    choice = ask('請選擇：')
    if choice == '1':
        preview(config, md)
    elif choice == '2':
        build_deck(config, md)


def help_menu(config: dict, repo: Path) -> None:
    header('說明')
    print(' [1] 在瀏覽器開啟語法速查（線上版）')
    print(' [2] 用記事本開啟語法速查（本機版）')
    print(' [3] 生成並開啟格式參考')
    print(' [0] 回上一層（直接按 Enter 也可以）')
    choice = ask('請選擇：')
    if choice == '1':
        webbrowser.open(CHEATSHEET_URL)
    elif choice == '2':
        open_in_text_editor(repo / 'docs' / '語法速查.md')
    elif choice == '3':
        output = brief_dir(config) / '說明' / '格式參考.html'
        output.parent.mkdir(parents=True, exist_ok=True)
        html = build(repo / 'docs' / '格式參考.md', output)
        if html:
            open_in_browser(html)
        pause()


def copy_example(config: dict, repo: Path) -> Path:
    """把範例複製到 brief/範例/；已存在的檔案不覆蓋"""
    folder = brief_dir(config) / '範例'
    (folder / 'images').mkdir(parents=True, exist_ok=True)
    md = folder / '範例.md'
    if not md.exists():
        shutil.copyfile(repo / 'examples' / 'example.md', md)
    for image in (repo / 'examples' / 'images').iterdir():
        target = folder / 'images' / image.name
        if image.is_file() and not target.exists():
            shutil.copyfile(image, target)
    return md


def generate_example(config: dict, repo: Path) -> None:
    md = copy_example(config, repo)
    build_deck(config, md)


def settings(config: dict) -> None:
    while True:
        header('設定')
        print(f'簡報資料夾：{brief_dir(config)}')
        print(f'設定檔：{config_path()}\n')
        print(' [1] 變更簡報資料夾')
        print(' [2] 清除最近使用清單')
        print(' [0] 回上一層（直接按 Enter 也可以）')
        choice = ask('請選擇：')
        if choice in ('', '0'):
            return
        if choice == '1':
            try:
                folder = pick_folder_dialog(brief_dir(config))
            except GuiUnavailable:
                text = clean_path(ask('請輸入新的簡報資料夾（直接按 Enter 取消）：'))
                folder = Path(text).expanduser() if text else None
            if folder:
                folder.mkdir(parents=True, exist_ok=True)
                config['brief_dir'] = str(folder.resolve())
                save_config(config)
                print(f'[OK] 簡報資料夾改為：{brief_dir(config)}（原本的簡報不會搬移）')
                pause()
        elif choice == '2':
            clear_recent(config)
            print('[OK] 已清除最近使用清單')
            pause()


# --- 主程式 --------------------------------------------------------------------

MENU = [
    ('1', '開啟 / 生成簡報'), ('2', '即時預覽'), ('3', '新增簡報'), ('4', '轉換舊簡報'),
    ('5', '開啟簡報資料夾'), ('6', '說明'), ('7', '生成範例'), ('8', '設定'), ('0', '結束'),
]


def show_menu(config: dict) -> None:
    header(f'HTML 簡報生成器 v{__version__}')
    print(f'簡報資料夾：{brief_dir(config)}\n')
    for key, label in MENU:
        print(f' [{key}] {label}')
    print()


def run_action(choice: str, config: dict, repo: Path) -> None:
    actions = {
        '1': lambda: build_deck(config),
        '2': lambda: preview(config),
        '3': lambda: new_deck(config, repo),
        '4': lambda: migrate(config, repo),
        '5': lambda: open_folder(brief_dir(config)),
        '6': lambda: help_menu(config, repo),
        '7': lambda: generate_example(config, repo),
        '8': lambda: settings(config),
    }
    if choice in actions:
        actions[choice]()


def handle_dropped(args: List[str], config: dict) -> None:
    """拖曳到 start.bat 的檔案：.md 直接即時預覽，其他顯示錯誤後回到選單"""
    if len(args) > 1:
        print(f'一次只能處理一個檔案，只開啟第一個：{args[0]}')
    path = Path(clean_path(args[0]))
    error = check_markdown(path)
    if error:
        print(f'[FAIL] {error}')
        pause()
        return
    preview(config, path)


def main(repo: Path, args: Optional[List[str]] = None) -> None:
    config = load_config()
    try:
        try:
            if ensure_brief_dir(config):
                print(f'已建立簡報資料夾：{brief_dir(config)}')
                print('之後新增的簡報都會放在這裡，可以在「設定」修改位置。')
                pause()
            if args:
                handle_dropped(args, config)
        except (EOFError, KeyboardInterrupt):
            raise
        except Exception as error:  # 啟動時的錯誤也顯示訊息後進入選單
            print(f'\n[FAIL] 發生錯誤：{type(error).__name__}: {error}')
        while True:
            show_menu(config)
            try:
                choice = ask('請選擇：')
            except KeyboardInterrupt:
                break
            if choice == '0':
                break
            try:
                run_action(choice, config, repo)
            except KeyboardInterrupt:
                print('\n已取消，回到選單')
            except EOFError:
                raise
            except Exception as error:  # 任何錯誤都顯示訊息後回到選單
                print(f'\n[FAIL] 發生錯誤：{type(error).__name__}: {error}')
                pause()
    except (EOFError, KeyboardInterrupt):
        pass
    print('\n謝謝使用！\n')
