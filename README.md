# briefgen：Markdown 轉 HTML 簡報

用 Markdown 快速打字做簡報：只在行首標格式，不寫結尾標籤。生成的是單一 HTML 檔，用瀏覽器直接播放，支援翻頁器，也能列印成 PDF。

3.0 起語法與舊版不相容，舊簡報請見[更新紀錄](CHANGELOG.md)與[使用指南的舊簡報轉換](docs/使用指南.md#舊簡報轉換)。

## 安裝

需要 Python 3.9 以上。在專案資料夾執行一次：

```bash
pip install -e .
```

Windows 也可以雙擊 `start.bat`，用中文選單操作：簡報集中放在「文件」資料夾底下的 `brief`，每份簡報一個資料夾，圖片放在裡面的 `images`。把 .md 檔拖到 `start.bat` 上會直接開始即時預覽。

## 30 秒上手

建立 `講義.md`：

```markdown
# 我的第一份簡報
## 副標題寫在這裡

- 行首的 "- " 是清單
- <b color=yellow>行首的角括號是格式，不用寫結尾

---

# 第二頁
## 用 --- 分頁

<imp>重要的話放進框裡
```

生成 HTML，或開啟即時預覽（存檔後瀏覽器自動更新，按 Ctrl+C 結束）：

```bash
briefgen build -i 講義.md -o 講義.html
briefgen watch 講義.md
```

## 文件

- [使用指南](docs/使用指南.md)：安裝、啟動器、命令列、上台操作、列印、圖片、舊簡報轉換、常見問題
- [語法速查](docs/語法速查.md)：一頁式表格，打字時快速查閱
- [格式參考](docs/格式參考.md)：用簡報展示所有格式，可以直接生成來看效果
- [範例簡報](examples/example.md)與[空白範本](examples/template.md)
- [開發](docs/開發.md)：架構、測試、golden 更新流程、CI
- [更新紀錄](CHANGELOG.md)
- 授權：MIT，見 [LICENSE](LICENSE)
