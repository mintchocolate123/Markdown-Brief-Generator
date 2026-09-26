# CLAUDE.md

Markdown 轉 HTML 簡報生成器。

## 常用指令

```bash
pip install -r requirements-dev.txt
python -m pytest                                    # pyproject.toml 已設定 pythonpath=src,tools
PYTHONPATH=src python -m briefgen build -i examples/example.md -o out.html
python tools/migrate_syntax.py 舊.md -o 新.md
```

## 架構

原始碼在 `src/briefgen/`，資料流：

1. `parsing/slides.py`：以單獨一行 `---` 切割投影片，取出 `# ` 標題與 `## ` 副標題；
   ``` 程式碼區塊內的 `---` 與 `#` 不影響分頁和標題（轉換工具共用同一套切法），
   `Slide.source_lines` 記錄每個內容行在原始檔的行號（不寫入 JSON）
2. `parsing/blocks.py`：`MarkdownParser.parse()` 抽出程式碼、`[table]`、`[tree]` 區塊，
   以 `[BLOCK_REF:key]` 佔位，並回傳每行的原始行索引；樹節點文字在這裡解析
3. `tags.py`：`parse_format()` 是唯一的行首格式解析，段落、儲存格、樹節點共用；
   回傳 styles 與區塊層級欄位，錯誤不丟例外，而是放進 `warnings`
4. `render/html.py`：`HTMLRenderer` 渲染段落（含 cont 接續）與區塊，
   警告依行號排序後交給 `warn` callback
5. `generator.py`：`PresentationGenerator` 載入 Markdown/JSON、套用
   `templates/template.html`，把警告以 `檔名:行號: 訊息` 印到 stderr
6. `cli.py` / `__main__.py`：`python -m briefgen new|build|export-slides`

其他：
- `launcher.py`、`start.bat` 留在根目錄，以 `python -m briefgen` 並設定 `PYTHONPATH=src` 呼叫
- `tools/migrate_syntax.py`：舊語法轉換，已是新語法的內容不變（可重複執行）
- `docs/格式參考.md` 是唯一的格式說明，本身也是簡報；`examples/example.md` 是範例

## 測試

- `tests/golden/*.html` 是 `tests/fixtures/new/*.md` 的預期輸出，必須逐字相同；
  每份 fixture 預期的警告列在 `tests/test_golden.py` 的 `EXPECTED_WARNINGS`
- `tests/fixtures/old/` 是舊語法版本，轉換後必須等於 `fixtures/new/`
- 改變輸出時，先列出 golden diff 給使用者確認，再重新產生 golden
- `docs/格式參考.md` 與 `examples/example.md` 生成時不可有警告

## 限制

- 不改視覺樣式（inline style 字串）、不加 emoji
- 每個 edge case 只測一件事

## 格式語法（設計意圖，優先於現有程式行為）

目的：快速打字做簡報。只在行首標格式，不寫結尾標籤。

### 行首格式
- 每行行首最多一個 `<...>`，裡面用空白分隔多個格式
  `<pivot=c size=6 color=orange>大標題`
- 無參數的格式直接寫名稱：`<b i>`、`<ct>`、`<imp>`、`<cont>`
- 有參數的格式寫 `name=value`，只切第一個 `=`：`<link=https://a.com/?x=1>`
- 值含空白時用雙引號：`<color="rgb(255, 0, 0)">`
- 標籤的結尾是雙引號外的第一個 `>`
- 名稱必須完全比對已知格式；只要有一個名稱不認識，整行視為普通文字，並在 stderr 印出警告與行號
- 名稱認得但值不合法（`size=9`、`pivot=x`、`tab=abc`、`b=1`、`color` 沒給值、`img` 欄位數不對），同未知名稱：整行當文字並警告
- 同一名稱重複時後者覆蓋前者，不警告：`<color=red color=blue>` 為藍色
- 行首的 `\<` 表示字面上的 `<`，不解析（先去掉行首空白再判斷；儲存格與樹節點文字同樣適用）
- 角括號沒有結尾（沒有 `>`）時整行當文字；若第一個 token 是已知名稱則警告（抓漏打 `>` 的手誤）
- 空的 `<>` 當文字並警告
- 格式後面緊接另一個 `<...>`（如 `<b><i>文字`）時，第二個 `<...>` 是字面文字，並警告可能是舊語法
- 格式 `>` 後面的空白會 strip（`cont` 行除外）

### cont（接續上一行）
用來在同一行中途換格式：

    第一段文字
    <cont color=red>紅色的接續文字

- 接續行變成上一行 `<div>` 裡的 `<span>`，只套文字層級格式：b、i、u、s、size、color、link
- 區塊層級格式（pivot、tab、ct、imp）由第一行決定，作用於整行包含所有接續段（imp 的接續段在框內）
- 文字層級格式（b、i、u、s、size、color、link）只作用於各自那一段，不繼承；
  有接續段時第一段的文字層級格式包在自己的 `<span>` 裡
- 區塊層級格式（pivot、tab、imp、ct、img）寫在 cont 行時忽略並警告
- 表格或程式碼區塊後緊接的 cont 行視為段落第一行
- cont 行 `>` 後面的空白保留，不 strip，讓英文可以寫 `<cont b> word`
- 段落第一行是 cont 時當普通行處理並警告
- 儲存格和樹節點不支援 cont，出現時警告
- 連續多行 cont 全部接在同一個 `<div>` 裡

### 已知格式
b / bold、i / italic、u / underline、s / strike、ct、imp、cont、
tab=N、pivot=l|c|r、size=1..7、color=名稱或色碼、link=網址、img=網址,寬,高

### 區塊標記
`[table]...[/table]`、`[tree]...[/tree]`，參數同樣用 `=`：
`[width=full]`、`[width=400px]`、`[id=2 p=1]`、`[c]`
方括號只用於區塊，不屬於行首格式。段落行首的 `[...]` 是普通文字。
- 樹節點方括號只接受 `id`、`p`；其他設定（如未轉換的 `o=1/2`）警告並忽略該項，節點照樣建立

### 警告
- 印到 stderr，Markdown 檔為 `檔名:行號: 訊息`，JSON 專案為 `投影片 N 第 M 行: 訊息`
- 行號是原始檔案中的行號

### 已廢除
- `<a><b>`（一行多個角括號）與 `name<arg>`（角括號參數）
- 樹節點方括號中的 `o<1/2>` 與 `imp`
- 舊檔用 `tools/migrate_syntax.py` 轉換；被移除的內容會列在轉換報告中
