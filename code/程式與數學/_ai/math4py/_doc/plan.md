
Python 的數學套件很混亂， math4py 企圖成為 Python 大統一的數學套件。

1. numpy/sympy/matplotlib 裡面有的，本套件就不創建，直接使用 numpy/sympy/matplotlib
    * 這些套件不足的部分，math4py 要去補充，例如 plot 套件，要能支援中文字型（跨平台設定）
2. numpy/sympy/matplotlib 沒有的數學函數，收錄到本套件中，盡量包裝得好用，有一致性
    * scipy 我覺得做得不好，非常混亂，我們重新用 R 的角度來建構
3. 核心數學區分為代數 algebra/ ，幾何 geometry/ 微積分 calculus/ 機率統計 statistic/ 
    * 線性代數放在 matrix/ 中(要包含矩陣，特徵值， SVD 分解等等)
    * 張量已經由 numpy 和 sympy 處理了，不夠的地方，請補在 tensor/ 下
    * statistics/ 採用 R 的函式庫語法設計，盡量和 R 相容一致
4. lean/ 採用類似 lean4 mathlib 的設計模式，主要用來做數學證明與定理檢驗。(這和其他套件有明顯區別)
5. 代數，幾何，微積分，機率統計，矩陣，線性代數，數學規劃，微分方程，傅立葉級數與轉換，隨機微積分，複變函數，向量微積分，泛函分析，微分幾何（可作為相對論基礎），拓樸學等等，都要納入到一個統一的框架當中，有一致性的物件和函數設計。
    * 這些在 sympy/numpy/matplotlib 中有處理的，可以適當在 math4py 中包裝後，讓他更好用。
6. 最後加入 math4py/physics 模組，用來包含『傳統力學，光學，電磁學，量子力學，相對論』
