# 行內格式
## 多個角括號與參數

<b><i>粗體斜體
<u><s>底線加刪除線
<size<4>><color<red>><b>紅色粗體
<color<red>><color<blue>>後者覆蓋

<i u color<green>>同一個角括號內多個格式
<link<i>>連結被誤判為斜體
<link<https://example.com/a?x=1>>含參數的連結
<img<https://example.com/a.png,300,150>>

---

# 方括號與空白
## 段落行首

[注意]方括號開頭的段落
[b]方括號粗體
[b] <i>方括號後接角括號
<b>   標籤後有空白
<tab<1>><pivot<r>>靠右縮排

---

# cont
## 接續上一行

第一段文字
<cont><color<red>>紅色的接續文字
<cont b> word

<cont>段落第一行就是接續

[table]
區塊
[/table]
<cont>區塊後緊接的接續

---

# 表格邊界
## 儲存格

[table]
[width<full>]
<imp>標題
[c]<b><i>多個角括號
[c]<imp> 前導空白
[注意]方括號開頭
[c]<color<green>>綠色
[c]<cont>儲存格接續
<size<2>>小字
[c]<link<i>>儲存格連結
[c]<u><s>雙線
[/table]

---

# 樹狀邊界
## 樹節點

[tree]
[id<1> imp] <b><i>根節點
[id<2> p<1> o<1/2>] <imp> 前導空白
[id<3> p<1> o<2/2>] [注意]方括號開頭
[id<4> p<2>] <color<red>><u>紅色底線
[/tree]

---

# 樹狀四層
## 任意深度

[tree]
[id<1>] 第一層
[id<2> p<1>] 第二層
[id<3> p<2>] 第三層
[id<4> p<3>] 第四層
[/tree]

---

# 程式碼
## 寬度與角括號

```cpp
[width<600px>]
#include <vector>
<html>
std::vector<int> v;
```

---

# 程式碼內的註解
## 不會變成標題

```py
# Python 註解
## 另一行註解
x = 1
```

---

# 程式碼內的分隔線
## 不會分頁

```text
上半
---
下半
```

---

# 清單
## 項目符號

- 第一層
  - 兩個空白是第二層
	- Tab 是第二層
   - 三個空白也是第二層

- <b>項目後接格式

- <pivot=c>項目不支援區塊格式

- 項目
<cont color=red>接續同一項

\- 不是清單

-沒有空白不是清單

[table]
- 儲存格不是清單
[/table]

[tree]
[id=1] - 樹節點不是清單
[/tree]

---

# 程式碼語言標記
## c++ 與 c#

```c++
std::vector<int> v;
```

```c#
string s = "c#";
```

---

## 只有副標題

副標題放在主標題的位置
