# HTML 簡報生成器

> **3.0 版的格式語法與舊版不相容。** 舊語法（如 `<size<5>><b>`、`[width<400px>]`）
> 的簡報請用 `tools/migrate_syntax.py` 轉換，見「舊簡報如何用 migrate_syntax.py 轉換」。
> 舊版程式保留在 tag [`v2-legacy-syntax`](https://github.com/mintchocolate123/Markdown-Brief-Generator/tree/v2-legacy-syntax)。

一個支援 Markdown 格式的網頁簡報生成工具，具有語法高亮、表格、樹狀圖等進階功能。

## 專案結構

```
.
├── src/briefgen/
│   ├── __main__.py          # python -m briefgen 進入點
│   ├── cli.py               # 命令列介面
│   ├── generator.py         # PresentationGenerator（載入/儲存、生成 HTML）
│   ├── model.py             # 資料模型（Slide, Presentation, SlideTheme）
│   ├── tags.py              # 行首格式解析（行內、儲存格、樹節點共用）
│   ├── highlighter.py       # 程式碼語法高亮
│   ├── parsing/
│   │   ├── slides.py        # 將 Markdown 檔切成投影片
│   │   └── blocks.py        # 程式碼、表格、樹狀圖區塊
│   ├── render/
│   │   └── html.py          # HTML 渲染器
│   └── templates/
│       └── template.html    # Jinja2 模板
├── tools/
│   └── migrate_syntax.py    # 舊語法轉換工具
├── docs/
│   ├── 格式參考.md           # 格式說明（本身也是一份簡報）
│   └── 路徑使用指南.md
├── examples/
│   └── example.md           # 範例 Markdown 投影片
├── tests/                   # pytest 測試與 golden 檔
├── launcher.py              # 中文互動式啟動器
├── start.bat                # Windows 雙擊啟動
├── pyproject.toml           # 套件設定（pip install -e .）
├── requirements.txt         # 執行依賴
└── requirements-dev.txt     # 開發依賴（pytest）
```

## 安裝

在專案目錄執行一次：

```bash
pip install -e .
```

之後在任何目錄都可以使用 `briefgen` 指令（或 `python -m briefgen`）。

## 使用方式

最簡單的方式是雙擊 `start.bat`（或執行 `python launcher.py`），依選單操作。

命令列中的 `briefgen` 也可以寫成 `python -m briefgen`（例如 Python 的 Scripts 目錄不在 PATH 時）。

### 1. 建立新專案

```bash
briefgen new -o my_presentation.json --title "我的簡報"
```

### 2. 從 Markdown 生成簡報

```bash
briefgen build -i examples/example.md -o output.html
```

### 3. 從 JSON 專案生成簡報

```bash
briefgen build -i my_presentation.json -o output.html
```

### 4. 匯出個別投影片 HTML

```bash
briefgen export-slides -i examples/example.md -o slides_output/
```

### 5. 使用自訂模板

```bash
briefgen build -i examples/example.md -o output.html --template custom_template.html
```

## Markdown 格式說明

只在行首寫一個 `<...>`，裡面用空白分隔多個格式，不寫結尾：

```markdown
<pivot=c size=6 color=orange>置中的大標題
<b i>粗體+斜體
第一段文字
<cont color=red>接在同一行的紅色文字
```

完整說明見 [docs/格式參考.md](docs/格式參考.md)。它本身也是一份簡報，可以直接生成來看效果：

```bash
briefgen build -i docs/格式參考.md -o 格式參考.html
```

格式寫錯時（名稱不認識、值不合法），該行會照原樣顯示，並在 stderr 印出 `檔名:行號: 訊息`。

## 舊簡報如何用 migrate_syntax.py 轉換

舊版語法（`<size<5>><b>`、`[width<400px>]`、`[id<2> p<1>]`）已廢除，請用轉換工具改寫：

```bash
python tools/migrate_syntax.py 舊簡報.md -o 新簡報.md
# 或直接覆寫
python tools/migrate_syntax.py 舊簡報.md --in-place
```

| 舊語法 | 新語法 |
|---|---|
| `<size<5>><color<red>><b>文字` | `<size=5 color=red b>文字` |
| `<link<https://a.com>>文字` | `<link=https://a.com>文字` |
| `[width<400px>]` | `[width=400px]` |
| `[id<2> p<1> o<1/2>]` | `[id=2 p=1]` |

轉換報告會印在 stderr，列出被移除或需要留意的內容，例如：

- 舊版沒有作用、新語法也不接受的格式（如 `size<9>`、未知名稱）會被移除
- 樹節點的 `o<...>` 與 `imp` 已廢除，會被移除
- 段落行首的 `[注意]` 這類方括號，舊版會被隱藏，新語法會顯示為文字

轉換後建議生成一次，確認沒有格式警告。

## 模組化設計

### model.py
定義資料結構：
- `Slide` - 單張投影片
- `Presentation` - 簡報專案
- `SlideTheme` - 主題配色

### parsing/slides.py
以 `---` 切割投影片，取出 `#` 標題與 `##` 副標題，並記錄每行在原始檔的行號（供警告使用）。

### parsing/blocks.py
提取特殊區塊：
- 程式碼區塊
- 表格區塊
- 樹狀圖區塊

### tags.py
解析行首格式 `<...>`，段落、表格儲存格、樹節點共用同一套規則。

### highlighter.py
程式碼語法高亮：
- 關鍵字辨識
- 字串/註解/數字上色
- 多語言支援

### render/html.py
渲染投影片為 HTML：
- 套用格式
- 渲染區塊內容
- 處理 cont 接續

### generator.py / cli.py
- 載入/儲存專案
- 組合 Jinja2 模板
- 生成最終 HTML、印出格式警告
- 命令列介面

## 進階功能

### 自訂主題

修改 `src/briefgen/model.py` 中的 `SlideTheme` 預設值，或在程式中動態設定：

```python
from briefgen.model import Presentation, SlideTheme

presentation = Presentation()
presentation.theme = SlideTheme(
    primary_color="#ff6b6b",
    secondary_color="#4ecdc4",
    accent_color="#ffe66d",
    bg_start="#1a1a2e",
    bg_mid="#16213e",
    bg_end="#0f3460"
)
```

### 批次處理

```python
from briefgen.generator import PresentationGenerator

gen = PresentationGenerator()
gen.load_from_markdown('slides.md')
gen.generate_html('output.html')
gen.generate_individual_slides('slides/')
```

## 測試

```bash
pip install -e . -r requirements-dev.txt
python -m pytest
```

`tests/golden/` 存放預期的 HTML 輸出，生成結果必須與它逐字相同。

## 鍵盤操作

生成的簡報支援以下鍵盤操作：
- `→` 或 `空白鍵` - 下一張
- `←` - 上一張
- 或使用螢幕按鈕控制

## 與原版的差異

### 改進項目

1. **模組化架構** - 分離關注點，每個模組負責單一功能
2. **Markdown 支援** - 使用標準 Markdown 語法（```）
3. **命令列工具** - 移除 GUI，改用 CLI
4. **Jinja2 模板** - 可自訂 HTML 模板
5. **獨立投影片** - 可匯出每張投影片為獨立 HTML
6. **型別提示** - 使用 Python type hints
7. **資料類別** - 使用 @dataclass 簡化模型

### 保留功能

- 所有格式（語法改為 `<size=5 color=red>`，舊檔請見「舊簡報如何用 migrate_syntax.py 轉換」）
- 程式碼語法高亮
- 表格與樹狀圖
- 主題配色系統

## 授權

MIT License
