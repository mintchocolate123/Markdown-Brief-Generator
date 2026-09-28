# 遞迴
## 讓函式呼叫自己

<pivot=c size=5>用階乘認識遞迴

<pivot=c color=gray>程式設計入門・第 7 週

---

# 什麼是遞迴
## 把大問題拆成同樣的小問題

<ct>遞迴的兩個部分

- 終止條件：
<cont b color=yellow>問題小到可以直接回答
- 遞迴呼叫：
<cont b color=cyan>用更小的同一個問題呼叫自己

<imp>每一次呼叫，問題都必須變得更小

---

## 生活中的例子

- 查字典時，解釋裡又有看不懂的詞，就再去查那個詞
- 打開俄羅斯娃娃，裡面還有一個更小的
  - 直到最小的那個打不開為止
  - 這個「打不開」就是終止條件

---

# 階乘
## n! = n × (n-1)!

```py
def factorial(n):
    if n <= 1:                    # 終止條件
        return 1
    return n * factorial(n - 1)   # 遞迴呼叫
print(factorial(5))               # 120
```

<ct>重點

- 第 2、3 行是終止條件
- 第 4 行用更小的 n 呼叫自己

---

# 呼叫過程
## factorial(3) 怎麼算出來

[tree]
[width=full]
[id=1] 3 × factorial(2)
[id=2 p=1] 2 × factorial(1)
[id=3 p=2] <color=yellow>回傳 1
[/tree]

<pivot=c>碰到終止條件後，結果一路往回乘：1 → 2 → 6

---

# 呼叫堆疊
## 每一層都在等下一層回傳

<img=images/call-stack.svg,480,auto>

- 每呼叫一次就疊一層，碰到終止條件後才一層一層回傳

---

# 遞迴還是迴圈
## 同一個問題的兩種寫法

[table]
[width=full]
<imp>比較
[c]<imp>遞迴
[c]<imp>迴圈
寫法
[c]貼近數學定義，通常較短
[c]需要自己管理計數變數
記憶體
[c]每一層呼叫都佔用堆疊
[c]通常比較省
適合
[c]樹狀結構、分而治之
[c]單純的重複計算
[/table]

---

# 常見錯誤
## 忘了讓問題變小

```py
def countdown(n):
    print(n)
    countdown(n - 1)   # 沒有終止條件，永遠不會停
```

<imp>Python 預設大約 1000 層後會停下來，出現
<cont b color=red> RecursionError

- 先寫終止條件，再寫遞迴呼叫
- 確認每次呼叫的參數都更接近終止條件

---

# 練習
## 動手寫寫看

- 用遞迴計算 1 + 2 + … + n
- 用遞迴把字串反轉
  - 提示：把第一個字元放到最後
- 挑戰：用遞迴算出費氏數列的第 n 項

<pivot=c size=4 color=orange>下週：用遞迴走訪資料夾裡的所有檔案
