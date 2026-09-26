# 行內格式
## 多個角括號與參數

<b><i>粗體斜體
<u><s>底線加刪除線
<size<4>><color<red>><b>紅色粗體
<color<red>><color<blue>>後者覆蓋
<cont color<red>>同一個角括號內多個格式
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

# 程式碼
## 寬度與角括號

```cpp
[width<600px>]
#include <vector>
<html>
std::vector<int> v;
```
