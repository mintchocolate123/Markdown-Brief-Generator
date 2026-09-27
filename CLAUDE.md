# CLAUDE.md

Markdown 轉 HTML 簡報生成器。

## 常用指令

```bash
pip install -e . -r requirements-dev.txt
python -m playwright install chromium               # e2e 測試用
python -m pytest                                    # pyproject.toml 已設定 pythonpath=src,tools
briefgen build -i examples/example.md -o out.html   # 等同 python -m briefgen
briefgen watch examples/example.md --no-open         # 即時預覽
python tools/migrate_syntax.py 舊.md -o 新.md
```

## 架構

原始碼在 `src/briefgen/`，資料流：

1. `parsing/slides.py`：以單獨一行 `---` 切割投影片，取出 `# ` 標題與 `## ` 副標題；
   ``` 程式碼區塊內的 `---` 與 `#` 不影響分頁和標題（轉換工具共用同一套切法），
   `Slide.source_lines` 記錄每個內容行在原始檔的行號（供警告使用）
2. `parsing/blocks.py`：`MarkdownParser.parse()` 抽出程式碼、`[table]`、`[tree]` 區塊，
   以 `[BLOCK_REF:key]` 佔位，並回傳每行的原始行索引；樹節點文字在這裡解析
3. `tags.py`：`parse_format()` 是唯一的行首格式解析，段落、儲存格、樹節點共用；
   回傳 styles 與區塊層級欄位，錯誤不丟例外，而是放進 `warnings`
4. `render/html.py`：`HTMLRenderer` 渲染段落（含 cont 接續、清單）與區塊（樹狀圖任意深度），
   警告依行號排序後交給 `warn` callback
5. `generator.py`：`PresentationGenerator` 載入 Markdown、套用
   `templates/template.html`，把警告以 `檔名:行號: 訊息` 印到 stderr
6. `cli.py` / `__main__.py`：`briefgen build` 與 `briefgen watch`（`python -m briefgen ...`）
7. `watch.py`：即時預覽，輪詢修改時間 + `http.server`；live reload 只插在伺服器回應的頁面，
   寫到磁碟的 HTML 不含；生成失敗保留上一個成功的版本，只有警告時照常更新並在角落列出

`templates/template.html` 除了版面，還負責瀏覽器端行為：
- 按鍵（→ ← ↓ ↑ 空白 PageUp/PageDown Home End F B）、網址 hash `#N`（replaceState）、黑屏遮罩
- `fitTrees()`：樹狀圖比卡片寬時以 `zoom` 等比例縮小
- 列印：`@media print` 與 `html.print-layout` 由 Jinja macro `print_rules` 產生同一份規則；
  `beforeprint` 套用列印版面後縮放樹狀圖與過高的投影片，`afterprint` 還原
- `highlighter.py`：每個語言一組有順序的 token 規則（字串、註解等），不支援的語言不上色

其他：
- `launcher.py`、`start.bat` 留在根目錄，以 `python -m briefgen` 呼叫；未安裝套件時提示 `pip install -e .`
- 版本號只寫在 `src/briefgen/__init__.py` 的 `__version__`，pyproject 與 launcher 由此讀取
- `tools/migrate_syntax.py`：舊語法轉換，已是新語法的內容不變（可重複執行）
- `examples/example.md` 是教學風格的範例簡報，`examples/template.md` 是空白範本，圖片放 `examples/images/`

## 檔案與文件分工

| 檔案 | 內容 |
|---|---|
| `README.md` | 這是什麼、安裝、30 秒上手、文件連結（保持精簡，開發內容不放這裡） |
| `CHANGELOG.md` | 各版本變化，對應 git tag；尚未發版的改動寫在「未發布」 |
| `docs/使用指南.md` | 使用者的完整說明：安裝 → 啟動器 → build / watch → 上台 → 列印 → 圖片 → 舊簡報轉換 → 常見問題 |
| `docs/語法速查.md` | 一頁式語法表格 |
| `docs/格式參考.md` | 用簡報展示所有格式的範例 |
| `docs/開發.md` | 架構、測試、golden 更新流程、CI |
| `LICENSE` | MIT |

- 使用者文件的語法說明改了，要同步更新 `docs/語法速查.md` 與本檔的語法規格
- 文件用繁體中文，不用 emoji（顏文字可以）；docs/ 與 examples/ 的每份 .md 都必須能無警告生成
- 寫簡報（範例、格式參考）的慣例：一頁放不下就分到接續頁（只寫 `##` 的頁面），
  接續頁的副標題寫該頁的主題，不重複上一頁的大標題，也不寫「（續）」
- 「放得下」的標準：1280×720（16:9 全螢幕，和投影機、PDF 一致）扣掉底部導覽列後不需要捲動，
  由 `tests/e2e/test_fit.py` 檢查；程式碼範例本身太長時縮短或換短的範例，不把一段程式碼切到兩頁

## 測試

- `tests/golden/*.html` 是 `tests/fixtures/new/*.md` 的預期輸出，必須逐字相同；
  每份 fixture 預期的警告列在 `tests/test_golden.py` 的 `EXPECTED_WARNINGS`
- `tests/fixtures/old/` 是舊語法版本，轉換後必須等於 `fixtures/new/`
- 改變輸出時，先列出 golden diff 給使用者確認，再重新產生 golden
- commit 前必須確認 pytest 的結束碼為 0；不要把 pytest 的輸出接到 tail、head 等管線
  （管線會吞掉結束碼），要截短輸出就先存檔再看
- `docs/格式參考.md` 與 `examples/example.md` 生成時不可有警告
- `tests/e2e/`：playwright（Python）瀏覽器端測試；沒有瀏覽器時自動 skip，
  CI 設 `BRIEFGEN_REQUIRE_E2E=1` 讓它改為失敗。瀏覽器行為（按鍵、縮放、列印、watch）都在這裡驗證

## 限制

- 不改視覺樣式（inline style 字串）、不加 emoji
- 每個 edge case 只測一件事
- 終端輸出只用 cp950 可編碼的字元（狀態用 `[OK]`、`[FAIL]`，不用 ✓ ✗），不依賴系統編碼：
  命令列進入點一開始呼叫 `briefgen.console.use_utf8_output()`（launcher 內有同樣的函式）

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

### 清單
- 行首 `- `（減號加空白）為清單項目，後面可接行首格式：`- <b color=red>重點`
- 縮排每 2 個空白或 1 個 Tab 多一層（奇數空白無條件捨去）；項目符號依層級為 • ◦ ▪，
  符號大小跟著該項的 size，顏色固定白色
- 第一層的左邊距 2em（同舊的 `<tab=1>• `），每層再加 2em；換行時文字對齊在項目符號後（懸掛縮排）
- 清單項目只套文字層級格式；區塊層級格式（pivot、tab、imp、ct、img）與 cont 寫在項目上時忽略並警告
- cont 可以接在清單項目後面，當作同一項的接續
- 行首 `\-` 表示字面上的 `-`
- 表格儲存格與樹節點不支援清單，`- ` 是普通文字；`---` 分頁不受影響

### 已知格式
b / bold、i / italic、u / underline、s / strike、ct、imp、cont、
tab=N、pivot=l|c|r、size=1..7、color=名稱或色碼、link=網址、img=路徑或網址,寬,高

### 圖片
- `img=路徑或網址,寬,高`：寬高為整數（像素）或 `auto`，其他值整行當文字並警告；
  路徑有空白時整個值用雙引號：`<img="我的 圖片/a.png,400,auto">`
- 寬高都指定時以 `aspect-ratio` 保持寫的比例；保留 `max-width:100%`，縮小時高度等比例
- 指定高度時（不論有沒有寬度）都加 `object-fit:contain`：寫的比例和原圖不同、或寬度被 max-width 壓縮時，
  圖片完整顯示在框內，不變形
- 本機圖片的相對路徑以 .md 檔所在資料夾為基準，生成時嵌成 data URI（輸出是單一檔案，watch 同樣適用）
- `http://`、`https://`、`data:` 開頭的網址維持原樣，不下載
- 找不到檔案時警告（附行號），圖片位置顯示「找不到圖片：路徑」
- 嵌入的本機圖片超過 1 MB 時警告（檔名、大小、行號），建議先壓縮；不阻止生成

顏色名稱已針對深色卡片背景調亮，除 black 外對比至少 4.5:1（WCAG AA）：
red #ff9999、green #00d200、blue #adadff、purple #d79eff、gray #b6b6b6；
white、yellow、cyan、orange、pink 原本就足夠；black 維持 #000（不建議使用）；自訂色碼不調整。

### 區塊標記
`[table]...[/table]`、`[tree]...[/tree]`，參數同樣用 `=`：
`[width=full]`、`[width=400px]`、`[id=2 p=1]`、`[c]`
方括號只用於區塊，不屬於行首格式。段落行首的 `[...]` 是普通文字。
- 樹節點方括號只接受 `id`、`p`；其他設定（如未轉換的 `o=1/2`）警告並忽略該項，節點照樣建立

### 警告
- 印到 stderr，格式為 `檔名:行號: 訊息`（程式直接建立、沒有來源檔的投影片為 `投影片 N 第 M 行: 訊息`）
- 行號是原始檔案中的行號

### 已廢除
- `<a><b>`（一行多個角括號）與 `name<arg>`（角括號參數）
- 樹節點方括號中的 `o<1/2>` 與 `imp`
- 舊檔用 `tools/migrate_syntax.py` 轉換；被移除的內容會列在轉換報告中
