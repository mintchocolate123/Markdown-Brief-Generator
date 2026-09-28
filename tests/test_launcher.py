"""啟動器：路徑、設定、最近使用、選單流程（家目錄與「文件」一律換成暫存資料夾）"""

import json
import sys
import types
from pathlib import Path

import pytest

from briefgen import launcher

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def sandbox(tmp_path, monkeypatch):
    """家目錄、文件資料夾都在暫存資料夾；不開視窗、不開瀏覽器或檔案總管"""
    home, documents = tmp_path / 'home', tmp_path / 'documents'
    home.mkdir()
    documents.mkdir()
    monkeypatch.setenv('BRIEFGEN_HOME', str(home))
    monkeypatch.setenv('BRIEFGEN_DOCUMENTS', str(documents))
    monkeypatch.setenv('BRIEFGEN_NO_GUI', '1')
    opened = []
    monkeypatch.setattr(launcher.webbrowser, 'open', lambda url: opened.append(('browser', url)))
    monkeypatch.setattr(launcher, 'open_folder', lambda path: opened.append(('folder', path)))
    monkeypatch.setattr(launcher, 'open_in_text_editor', lambda path: opened.append(('editor', path)))
    return types.SimpleNamespace(home=home, documents=documents, brief=documents / 'brief', opened=opened,
                                 tmp=tmp_path)


def feed(monkeypatch, *answers):
    """依序回答 input()，回答完再問就視為輸入結束"""
    queue = list(answers)

    def fake_input(prompt=''):
        print(prompt, end='')
        if not queue:
            raise EOFError
        answer = queue.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        print(answer)
        return answer
    monkeypatch.setattr('builtins.input', fake_input)


def md_file(folder, name='講義', text='# 標題\n內容\n'):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{name}.md'
    path.write_text(text, encoding='utf-8')
    return path


# --- 路徑與設定 ------------------------------------------------------------------

def test_default_brief_dir_is_under_documents(sandbox):
    assert launcher.brief_dir(launcher.load_config()) == sandbox.brief


def test_config_file_is_in_home_not_repo(sandbox):
    assert launcher.config_path() == sandbox.home / '.briefgen' / 'launcher.json'
    launcher.save_config(launcher.load_config())
    assert launcher.config_path().is_file()
    assert not (ROOT / '.briefgen').exists()


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason='XDG 只在 Linux 使用')
def test_linux_uses_xdg_documents_dir(sandbox, monkeypatch):
    monkeypatch.delenv('BRIEFGEN_DOCUMENTS')
    config_home = sandbox.tmp / 'xdg'
    config_home.mkdir()
    (config_home / 'user-dirs.dirs').write_text('XDG_DOCUMENTS_DIR="$HOME/文件"\n', encoding='utf-8')
    monkeypatch.setenv('XDG_CONFIG_HOME', str(config_home))
    assert launcher.documents_dir() == sandbox.home / '文件'


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason='XDG 只在 Linux 使用')
def test_linux_without_xdg_uses_home_documents(sandbox, monkeypatch):
    monkeypatch.delenv('BRIEFGEN_DOCUMENTS')
    monkeypatch.setenv('XDG_CONFIG_HOME', str(sandbox.tmp / '沒有設定'))
    assert launcher.documents_dir() == sandbox.home / 'Documents'


@pytest.mark.skipif(sys.platform != 'win32', reason='只有 Windows 有 SHGetKnownFolderPath')
def test_windows_documents_from_system_api(monkeypatch):
    monkeypatch.delenv('BRIEFGEN_DOCUMENTS')
    path = launcher._windows_documents()
    assert path is not None and path.is_absolute() and path.is_dir()
    assert launcher.documents_dir() == path


def test_first_run_creates_brief_dir_and_says_where(sandbox, monkeypatch, capsys):
    feed(monkeypatch, '', '0')
    launcher.main(ROOT)
    out = capsys.readouterr().out
    assert sandbox.brief.is_dir()
    assert f'已建立簡報資料夾：{sandbox.brief}' in out
    assert f'簡報資料夾：{sandbox.brief}' in out
    assert '當前目錄' not in out


def test_corrupted_config_is_reset(sandbox):
    launcher.config_path().parent.mkdir(parents=True)
    launcher.config_path().write_text('{壞掉', encoding='utf-8')
    assert launcher.load_config() == {'brief_dir': '', 'recent': []}


# --- 最近使用 ------------------------------------------------------------------

def test_recent_keeps_five_most_recent_first(sandbox):
    config = launcher.load_config()
    files = [md_file(sandbox.tmp / 'decks', f'第{i}份') for i in range(7)]
    for path in files:
        launcher.add_recent(config, path)
    assert launcher.recent_files(config) == [p.resolve() for p in reversed(files[2:])]
    launcher.add_recent(config, files[3])
    assert launcher.recent_files(config)[0] == files[3].resolve()
    assert len(launcher.recent_files(config)) == 5
    saved = json.loads(launcher.config_path().read_text(encoding='utf-8'))['recent']
    assert saved[0] == str(files[3].resolve())


def test_missing_recent_files_are_removed(sandbox):
    config = launcher.load_config()
    keep, gone = md_file(sandbox.tmp, '留著'), md_file(sandbox.tmp, '刪掉')
    launcher.add_recent(config, keep)
    launcher.add_recent(config, gone)
    gone.unlink()
    assert launcher.recent_files(config) == [keep.resolve()]
    assert json.loads(launcher.config_path().read_text(encoding='utf-8'))['recent'] == [str(keep.resolve())]


def test_clear_recent(sandbox):
    config = launcher.load_config()
    launcher.add_recent(config, md_file(sandbox.tmp))
    launcher.clear_recent(config)
    assert launcher.load_config()['recent'] == []


# --- 名稱與備份 ----------------------------------------------------------------

@pytest.mark.parametrize('name', ['講義', '期中 報告', 'week-01_遞迴', 'v1.2'])
def test_valid_names(name):
    assert launcher.name_error(name) is None


@pytest.mark.parametrize('name', ['a/b', 'a\\b', 'a:b', 'a*b', 'a?b', 'a"b', 'a<b', 'a>b', 'a|b',
                                  '結尾句點.', '結尾空白 ', 'CON', 'nul', 'com1', 'LPT9.md', 'a\tb'])
def test_invalid_names(name):
    assert launcher.name_error(name)


def test_backup_names_do_not_overwrite(sandbox):
    md = md_file(sandbox.tmp)
    first = launcher.backup_path(md)
    assert first.name == '講義.v2.bak.md'
    first.write_text('舊備份', encoding='utf-8')
    second = launcher.backup_path(md)
    assert second.name == '講義.v2.bak-2.md'
    second.write_text('', encoding='utf-8')
    assert launcher.backup_path(md).name == '講義.v2.bak-3.md'


# --- 選檔 ----------------------------------------------------------------------

def test_choose_from_recent_by_number(sandbox, monkeypatch):
    config = launcher.load_config()
    a, b = md_file(sandbox.tmp, 'A'), md_file(sandbox.tmp, 'B')
    launcher.add_recent(config, a)
    launcher.add_recent(config, b)
    feed(monkeypatch, '2')
    assert launcher.choose_markdown(config, '測試') == a.resolve()


@pytest.mark.parametrize('answer', ['', '0'])
def test_choose_back_with_enter_or_zero(sandbox, monkeypatch, answer):
    feed(monkeypatch, answer)
    assert launcher.choose_markdown(launcher.load_config(), '測試') is None


def test_choose_with_file_dialog(sandbox, monkeypatch):
    md = md_file(sandbox.tmp)
    monkeypatch.delenv('BRIEFGEN_NO_GUI')
    monkeypatch.setattr(launcher, 'gui_available', lambda: True)
    monkeypatch.setattr(launcher, 'pick_file_dialog', lambda initial: md)
    feed(monkeypatch, 'F')
    assert launcher.choose_markdown(launcher.load_config(), '測試') == md


def test_file_dialog_only_shows_markdown_and_starts_in_brief(sandbox, monkeypatch):
    """以假的 tkinter 模組取代真正的視窗"""
    calls = {}

    class FakeTk:
        def withdraw(self): calls['withdraw'] = True
        def attributes(self, *args): calls['topmost'] = args
        def destroy(self): calls['destroyed'] = True

    def askopenfilename(**kwargs):
        calls['dialog'] = kwargs
        return str(sandbox.brief / '講義' / '講義.md')

    fake_tk = types.ModuleType('tkinter')
    fake_tk.Tk = FakeTk
    fake_dialog = types.ModuleType('tkinter.filedialog')
    fake_dialog.askopenfilename = askopenfilename
    fake_tk.filedialog = fake_dialog
    monkeypatch.setitem(sys.modules, 'tkinter', fake_tk)
    monkeypatch.setitem(sys.modules, 'tkinter.filedialog', fake_dialog)
    monkeypatch.delenv('BRIEFGEN_NO_GUI')

    chosen = launcher.pick_file_dialog(sandbox.brief)
    assert chosen == sandbox.brief / '講義' / '講義.md'
    assert calls['dialog']['initialdir'] == str(sandbox.brief)
    assert calls['dialog']['filetypes'] == [('Markdown 簡報', '*.md')]
    assert calls['topmost'] == ('-topmost', True) and calls['destroyed']


def test_without_gui_falls_back_to_typed_path_and_strips_quotes(sandbox, monkeypatch, capsys):
    md = md_file(sandbox.tmp / '有 空白')
    feed(monkeypatch, 'F', f'"{md}"')
    assert launcher.choose_markdown(launcher.load_config(), '測試') == md
    assert '可以把 .md 檔拖進這個視窗' in capsys.readouterr().out


def test_choosing_a_non_markdown_file_is_rejected(sandbox, monkeypatch, capsys):
    txt = sandbox.tmp / 'a.txt'
    txt.write_text('x', encoding='utf-8')
    feed(monkeypatch, 'F', str(txt), '', '0')
    assert launcher.choose_markdown(launcher.load_config(), '測試') is None
    assert '[FAIL] 只能選擇 .md 檔' in capsys.readouterr().out


# --- 選單流程 ------------------------------------------------------------------

def test_errors_return_to_menu(sandbox, monkeypatch, capsys):
    def broken(path):
        raise PermissionError('沒有權限')
    monkeypatch.setattr(launcher, 'open_folder', broken)
    feed(monkeypatch, '', '5', '', '0')
    launcher.main(ROOT)
    out = capsys.readouterr().out
    assert '[FAIL] 發生錯誤：PermissionError: 沒有權限' in out
    assert out.count('[5] 開啟簡報資料夾') == 2  # 錯誤後又回到選單


def test_ctrl_c_in_submenu_returns_to_menu(sandbox, monkeypatch, capsys):
    feed(monkeypatch, '', '8', KeyboardInterrupt(), '0')
    launcher.main(ROOT)
    out = capsys.readouterr().out
    assert '已取消，回到選單' in out and out.count('[8] 設定') == 2


def test_open_brief_folder(sandbox, monkeypatch):
    feed(monkeypatch, '', '5', '0')
    launcher.main(ROOT)
    assert sandbox.opened == [('folder', sandbox.brief)]


def test_new_deck_creates_folder_structure(sandbox, monkeypatch, capsys):
    feed(monkeypatch, '', '3', '講義', 'n', '0')
    launcher.main(ROOT)
    folder = sandbox.brief / '講義'
    assert (folder / '講義.md').read_text(encoding='utf-8') == \
        (ROOT / 'examples' / 'template.md').read_text(encoding='utf-8')
    assert (folder / 'images').is_dir()
    assert launcher.load_config()['recent'] == [str((folder / '講義.md').resolve())]


def test_new_deck_rejects_bad_and_existing_names_without_overwriting(sandbox, monkeypatch, capsys):
    existing = md_file(sandbox.brief / '講義', text='我的內容')
    feed(monkeypatch, '', '3', '講/義', '講義', '新的', 'n', '0')
    launcher.main(ROOT)
    out = capsys.readouterr().out
    assert '名稱不能包含' in out and '已經有同名的簡報資料夾' in out
    assert existing.read_text(encoding='utf-8') == '我的內容'
    assert (sandbox.brief / '新的' / '新的.md').is_file()


def test_new_deck_can_start_preview(sandbox, monkeypatch):
    started = []
    monkeypatch.setattr(launcher, 'preview', lambda config, md=None: started.append(md))
    feed(monkeypatch, '', '3', '講義', 'y', '0')
    launcher.main(ROOT)
    assert started == [sandbox.brief / '講義' / '講義.md']


def test_help_menu_options(sandbox, monkeypatch):
    feed(monkeypatch, '', '6', '1', '6', '2', '0')
    launcher.main(ROOT)
    assert sandbox.opened == [('browser', launcher.CHEATSHEET_URL),
                              ('editor', ROOT / 'docs' / '語法速查.md')]


def test_copy_example_does_not_overwrite(sandbox):
    config = launcher.load_config()
    md = launcher.copy_example(config, ROOT)
    assert md == sandbox.brief / '範例' / '範例.md'
    assert (sandbox.brief / '範例' / 'images' / 'call-stack.svg').is_file()
    md.write_text('我改過的範例', encoding='utf-8')
    launcher.copy_example(config, ROOT)
    assert md.read_text(encoding='utf-8') == '我改過的範例'


def test_settings_change_brief_dir(sandbox, monkeypatch):
    new_dir = sandbox.tmp / '新的 簡報資料夾'
    feed(monkeypatch, '', '8', '1', f'"{new_dir}"', '', '0', '0')
    launcher.main(ROOT)
    assert new_dir.is_dir()
    assert launcher.brief_dir(launcher.load_config()) == new_dir.resolve()


def test_settings_clear_recent(sandbox, monkeypatch):
    config = launcher.load_config()
    launcher.add_recent(config, md_file(sandbox.tmp))
    feed(monkeypatch, '', '8', '2', '', '0', '0')
    launcher.main(ROOT)
    assert launcher.load_config()['recent'] == []


def test_dropped_non_markdown_shows_error_then_menu(sandbox, monkeypatch, capsys):
    txt = sandbox.tmp / '筆記.txt'
    txt.write_text('x', encoding='utf-8')
    feed(monkeypatch, '', '', '0')
    launcher.main(ROOT, [str(txt)])
    out = capsys.readouterr().out
    assert '[FAIL] 只能選擇 .md 檔' in out and '[1] 開啟 / 生成簡報' in out


def test_dropped_markdown_starts_preview_first(sandbox, monkeypatch, capsys):
    md = md_file(sandbox.tmp)
    started = []
    monkeypatch.setattr(launcher, 'preview', lambda config, path=None: started.append(path))
    feed(monkeypatch, '', '0')
    launcher.main(ROOT, [str(md), str(sandbox.tmp / '第二個.md')])
    assert started == [md]
    assert '一次只能處理一個檔案' in capsys.readouterr().out


def test_help_builds_format_reference_into_brief(sandbox, monkeypatch):
    feed(monkeypatch, '', '6', '3', '', '0')
    launcher.main(ROOT)
    output = sandbox.brief / '說明' / '格式參考.html'
    assert output.is_file()
    assert sandbox.opened == [('browser', output.resolve().as_uri())]
    assert not (ROOT / 'docs' / '格式參考.html').exists()
