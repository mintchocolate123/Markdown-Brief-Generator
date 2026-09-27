# 更新紀錄

每個版本都對應一個 git tag，可以用 `git checkout v3.2` 這樣的指令取得當時的程式。

## 未發布

- 移除 `--template` 選項（沒有測試，而且自訂模板會失去按鍵、列印、樹狀圖縮放等功能）
- 移除 `requirements.txt`，執行依賴只寫在 `pyproject.toml`
- 新增 MIT 授權檔 `LICENSE`
- 文件重整：README 精簡；新增使用指南、語法速查、開發說明與本檔；範例改寫成教學簡報，新增空白範本

## v3.2

tag：[v3.2](https://github.com/mintchocolate123/Markdown-Brief-Generator/tree/v3.2)

- 只有 `##` 副標題的投影片也會顯示標題卡片，副標題放在主標題的位置
- 頁面 `<title>` 依序取第一張的 `#` 標題、`##` 副標題、檔名
- `migrate_syntax.py` 的報告列出寫在行中間、不會套用的標籤（附行號，提示拆成 cont 行）
- 圖片的寬高生效：`img=路徑或網址,寬,高`，寬高為像素或 `auto`；比例和原圖不同時完整顯示、不變形
- 本機圖片以 .md 檔所在資料夾為基準，生成時嵌入 HTML，輸出為單一檔案；找不到檔案或超過 1 MB 時警告
- 文件中的 emoji 改為文字符號，並以測試防止再混入

## v3.1

tag：[v3.1](https://github.com/mintchocolate123/Markdown-Brief-Generator/tree/v3.1)

- 上台操作：翻頁器（PageUp / PageDown）、長投影片先捲動再翻頁、Home / End、F 全螢幕、B 黑屏、網址 `#N` 記住頁數
- `briefgen watch` 即時預覽，啟動器新增「即時預覽」選項
- 列印 / PDF：每張投影片一頁 16:9，保留深色背景與程式碼配色，太寬或太長的內容等比例縮小
- 清單語法：行首 `- 項目`，每 2 個空白或 1 個 Tab 多一層
- 語法高亮新增 bash / sh、html、css、json；` ```c++ `、` ```c# ` 正確辨識
- 顏色名稱針對深色背景調亮，除 black 外對比至少 4.5:1
- 樹狀圖支援任意深度，連接線接到每個子節點，太寬時縮小放進卡片
- `--title` 沒指定時使用檔案自己的標題；指令錯誤以非 0 結束碼結束
- 終端輸出一律 UTF-8，狀態改用 `[OK]` / `[FAIL]`，在繁體中文 Windows 不再當掉
- 移除 JSON 專案、`new`、`export-slides` 指令，以及沒有作用的主題設定

## v3.0

tag：[v3.0](https://github.com/mintchocolate123/Markdown-Brief-Generator/tree/v3.0)

- 重整為 `briefgen` 套件，`pip install -e .` 後可在任何目錄使用 `briefgen` 指令
- 新的格式語法：行首一個 `<...>`，裡面用空白分隔 `name` 或 `name=value`，不寫結尾
- 新增 `cont`：在同一行中途換格式
- 格式寫錯時整行照原樣顯示，並在終端機印出 `檔名:行號: 訊息`
- 新增 `tools/migrate_syntax.py`，把舊語法轉換為新語法
- 程式碼區塊裡的 `#` 與 `---` 不再影響標題和分頁

## v2-legacy-syntax

tag：[v2-legacy-syntax](https://github.com/mintchocolate123/Markdown-Brief-Generator/tree/v2-legacy-syntax)

使用舊語法（`<size<5>><b>`、`[width<400px>]`）的最後版本。舊簡報請用 `tools/migrate_syntax.py` 轉換，見[使用指南](docs/使用指南.md#舊簡報轉換)。
