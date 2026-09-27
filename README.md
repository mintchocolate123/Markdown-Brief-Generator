# HTML 簡報生成器

> **3.0 版的格式語法與舊版不相容。** 舊語法（如 `<size<5>><b>`、`[width<400px>]`）
> 的簡報請用 `tools/migrate_syntax.py` 轉換，見「舊簡報如何用 migrate_syntax.py 轉換」。
> 舊版程式保留在 tag [`v2-legacy-syntax`](https://github.com/mintchocolate123/Markdown-Brief-Generator/tree/v2-legacy-syntax)。

一個支援 Markdown 格式的網頁簡報生成工具，具有語法高亮、表格、樹狀圖等進階功能。

**3.1 新增：** 上台操作（翻頁器、全螢幕、黑屏、網址記住頁數）、`briefgen watch` 即時預覽、
列印 / 輸出 PDF、清單語法（`- 項目`）、bash / html / css / json 語法高亮、樹狀圖任意深度；
顏色名稱針對深色背景調亮。JSON 專案、`new`、`export-slides` 指令已移除。

## 專案結構

```
.
├── src/briefgen/
│   ├── __main__.py          # python -m briefgen 進入點
│   ├── cli.py               # 命令列介面（build、watch）
│   ├── console.py           # 終端輸出設定（UTF-8）
│   ├── generator.py         # PresentationGenerator（載入 Markdown、生成 HTML）
│   ├── watch.py             # 即時預覽
│   ├── model.py             # 資料模型（Slide, Presentation）
│   ├── tags.py              # 行首格式解析（行內、儲存格、樹節點共用）
│   ├── highlighter.py       # 程式碼語法高亮
│   ├── parsing/
│   │   ├── slides.py        # 將 Markdown 檔切成投影片
│   │   └── blocks.py        # 程式碼、表格、樹狀圖區塊
│   ├── render/
│   │   └── html.py          # HTML 渲染器
│   └── templates/
│       └── template.html    # Jinja2 模板（按鍵操作、樹狀圖縮放、列印版面）
├── tools/
│   └── migrate_syntax.py    # 舊語法轉換工具
├── docs/
│   ├── 格式參考.md           # 格式說明（本身也是一份簡報）
│   └── 路徑使用指南.md
├── examples/
│   └── example.md           # 範例 Markdown 投影片
├── tests/                   # pytest 測試與 golden 檔；tests/e2e/ 為瀏覽器端測試
├── launcher.py              # 中文互動式啟動器
├── start.bat                # Windows 雙擊啟動
├── pyproject.toml           # 套件設定（pip install -e .）
├── requirements.txt         # 執行依賴
└── requirements-dev.txt     # 開發依賴（pytest、playwright、pypdfium2）
```

## 安裝

在專案目錄執行一次：

```bash
pip install -e .
```

之後在任何目錄都可以使用 `briefgen` 指令（或 `python -m briefgen`）。

## 使用方式

最簡單的方式是雙擊 `start.bat`（或執行 `python launcher.py`），依選單操作：
生成簡報、生成範例、即時預覽。

命令列中的 `briefgen` 也可以寫成 `python -m briefgen`（例如 Python 的 Scripts 目錄不在 PATH 時）。

### 1. 從 Markdown 生成簡報

```bash
briefgen build -i examples/example.md -o output.html
```

簡報標題（瀏覽器分頁上的 `<title>`）預設取第一張投影片的 `#` 標題，沒有時用 `##` 副標題，再沒有才用檔名（不含副檔名），
可用 `-t "標題"` 指定。

### 2. 使用自訂模板

```bash
briefgen build -i examples/example.md -o output.html --template custom_template.html
```

### 3. 即時預覽

```bash
briefgen watch examples/example.md
```

- 自動開啟瀏覽器；每次存檔都會重新生成，瀏覽器自動重新載入並停在原本那一張
- 生成的 HTML 寫在 Markdown 旁邊（`example.html`），可用 `-o` 指定；`--no-open` 不開瀏覽器，`--port` 指定埠號
- 格式有警告時頁面照常更新，並在右上角列出警告；生成失敗時保留上一個成功的版本並顯示錯誤
- 寫到磁碟的 HTML 不含即時預覽用的程式碼；按 Ctrl+C 結束

### 4. 列印 / 輸出 PDF

在瀏覽器開啟生成的 HTML，按 Ctrl+P（Mac 為 Cmd+P），目的地選「另存為 PDF」。

- 每張投影片一頁，16:9 橫式，不含導覽列與按鈕
- 保留深色背景與程式碼配色
- 太寬的樹狀圖、太長的投影片會等比例縮小放進一頁

## Markdown 格式說明

只在行首寫一個 `<...>`，裡面用空白分隔多個格式，不寫結尾：

```markdown
<pivot=c size=6 color=orange>置中的大標題
<b i>粗體+斜體
第一段文字
<cont color=red>接在同一行的紅色文字
```

- 清單：行首 `- 項目`，每 2 個空白（或 1 個 Tab）多一層
- 程式碼區塊支援語法高亮：c、cpp（c++）、cs（c#）、py、js、java、bash（sh）、html、css、json

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
- `Presentation` - 簡報（標題與投影片）

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

### watch.py
即時預覽：輪詢檔案修改時間、以 `http.server` 提供頁面，只在伺服器回應的頁面插入自動重新載入的程式碼。

### generator.py / cli.py
- 載入 Markdown
- 組合 Jinja2 模板
- 生成最終 HTML、印出格式警告
- 命令列介面

## 在程式中使用

```python
from briefgen.generator import PresentationGenerator

gen = PresentationGenerator()
gen.load_from_markdown('slides.md')
gen.generate_html('output.html')
```

## 測試

```bash
pip install -e . -r requirements-dev.txt
python -m playwright install chromium   # 瀏覽器端測試用
python -m pytest
```

- `tests/golden/` 存放預期的 HTML 輸出，生成結果必須與它逐字相同
- `tests/e2e/` 以 playwright 驗證按鍵操作、即時預覽、列印等瀏覽器行為；沒有安裝瀏覽器時會自動略過
  （CI 設定 `BRIEFGEN_REQUIRE_E2E=1`，缺少瀏覽器時改為失敗）

## 鍵盤操作

生成的簡報支援以下鍵盤操作（翻頁器送出的是 PageUp / PageDown）：

| 按鍵 | 動作 |
|---|---|
| `→` | 下一張 |
| `←` | 上一張 |
| `↓`、空白鍵、`PageDown` | 投影片還沒捲到底時先往下捲一個畫面，已在底部才翻到下一張 |
| `↑`、`PageUp` | 還沒捲到頂時先往上捲，已在頂部才翻回上一張 |
| `Home` / `End` | 第一張 / 最後一張 |
| `F` | 切換全螢幕 |
| `B` | 切換黑屏；黑屏時按翻頁鍵只會恢復畫面，不換頁 |

網址的 `#12` 記住目前頁數，重新整理或直接開啟 `簡報.html#12` 會停在第 12 張。

## 與原版的差異

### 改進項目

1. **模組化架構** - 分離關注點，每個模組負責單一功能
2. **Markdown 支援** - 使用標準 Markdown 語法（```）
3. **命令列工具** - 移除 GUI，改用 CLI
4. **Jinja2 模板** - 可自訂 HTML 模板
5. **型別提示** - 使用 Python type hints
6. **資料類別** - 使用 @dataclass 簡化模型

### 保留功能

- 所有格式（語法改為 `<size=5 color=red>`，舊檔請見「舊簡報如何用 migrate_syntax.py 轉換」）
- 程式碼語法高亮
- 表格與樹狀圖（3.1 起支援任意深度）

## 授權

MIT License
