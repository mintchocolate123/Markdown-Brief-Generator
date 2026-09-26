# HTML 簡報生成器

一個支援 Markdown 格式的網頁簡報生成工具，具有語法高亮、表格、樹狀圖等進階功能。

## 專案結構

```
.
├── slide_model.py           # 資料模型（Slide, Presentation, Theme）
├── markdown_parser.py       # Markdown 解析器
├── syntax_highlighter.py   # 程式碼語法高亮
├── html_renderer.py         # HTML 渲染器
├── presentation_generator.py # 主程式
├── template.html            # Jinja2 模板
├── requirements.txt         # 依賴套件
├── example.md              # 範例 Markdown 投影片
└── README.md               # 說明文件
```

## 安裝

```bash
pip install -r requirements.txt
```

## 使用方式

### 1. 建立新專案

```bash
python presentation_generator.py new -o my_presentation.json --title "我的簡報"
```

### 2. 從 Markdown 生成簡報

```bash
python presentation_generator.py build -i example.md -o output.html
```

### 3. 從 JSON 專案生成簡報

```bash
python presentation_generator.py build -i my_presentation.json -o output.html
```

### 4. 匯出個別投影片 HTML

```bash
python presentation_generator.py export-slides -i example.md -o slides_output/
```

### 5. 使用自訂模板

```bash
python presentation_generator.py build -i example.md -o output.html --template custom_template.html
```

## Markdown 格式說明

### 投影片分隔

使用 `---` 分隔不同投影片：

```markdown
# 第一張投影片
內容...

---

# 第二張投影片
內容...
```

### 標題

- `# 標題` - 主標題
- `## 副標題` - 副標題

### 文字格式

基本格式寫在 `<>` 內：

```markdown
<size<5>>大字體文字
<color<purple>>紫色文字
<b>粗體
<i>斜體
<u>底線
<s>刪除線
```

### 特殊區塊

```markdown
<ct>子標題
<imp>重要訊息區塊
<pivot<c>>置中對齊
<tab<2>>縮排 2 單位
<link<網址>>超連結
```

### 程式碼區塊

使用標準 Markdown 語法：

````markdown
```py
def hello():
    print("Hello")
```
````

支援語言：`c`, `cpp`, `cs`, `py`, `js`, `java`

可加入寬度設定：

````markdown
```py
[width<full>]
程式碼...
```
````

### 表格

```markdown
[table]
[width<400px>]
<imp>標題1
[c]<imp>標題2
資料1
[c]資料2
[/table]
```

### 樹狀圖

```markdown
[tree]
[width<full>]
[id<1>] 根節點
[id<2> p<1>] 子節點
[id<3> p<1>] 另一子節點
[/tree]
```

## 模組化設計

### slide_model.py
定義資料結構：
- `Slide` - 單張投影片
- `Presentation` - 簡報專案
- `SlideTheme` - 主題配色

### markdown_parser.py
解析 Markdown 內容，提取：
- 程式碼區塊
- 表格區塊
- 樹狀圖區塊
- 行內格式

### syntax_highlighter.py
程式碼語法高亮：
- 關鍵字辨識
- 字串/註解/數字上色
- 多語言支援

### html_renderer.py
渲染投影片為 HTML：
- 解析格式標記
- 渲染區塊內容
- 生成樣式

### presentation_generator.py
主程式：
- 載入/儲存專案
- 解析 Markdown
- 組合 Jinja2 模板
- 生成最終 HTML

## 進階功能

### 自訂主題

修改 `slide_model.py` 中的 `SlideTheme` 預設值，或在程式中動態設定：

```python
from slide_model import Presentation, SlideTheme

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
from presentation_generator import PresentationGenerator

gen = PresentationGenerator()
gen.load_from_markdown('slides.md')
gen.generate_html('output.html')
gen.generate_individual_slides('slides/')
```

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

- 所有格式標記（`<size<>>`, `<color<>>`, 等）
- 程式碼語法高亮
- 表格與樹狀圖
- 主題配色系統

## 授權

MIT License
