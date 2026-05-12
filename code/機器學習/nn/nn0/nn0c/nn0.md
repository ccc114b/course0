# nn0 — C 語言自動微分引擎與神經網路基礎元件

## 原理

nn0 是一個用 C 語言實作的自動微分引擎，提供數值運算節點（Value）的建構與反向傳播機制。它使用計算圖（Computation Graph）方式追蹤所有運算，並在反向傳播時透過鏈式法則自動計算梯度。此外也包含了 Adam 優化器、矩陣運算、Softmax、RMSNorm 等神經網路必備元件。

### 核心架構

1. **Value 節點**: 每個節點儲存資料值 (data)、梯度 (grad)、子節點指標與局部梯度
2. **計算圖**: 透過二元樹結構追蹤運算歷史
3. **拓樸排序**: 反向傳播時先對計算圖進行拓樸排序，確保梯度正確傳遞
4. **記憶體池 (Arena)**: 預先分配大區塊記憶體，避免大量 malloc/free 的開銷
5. **Adam 優化器**: 實作一階動量與二階動量的自適應學習率演算法

### 演算法步驟

**前向傳播**:
1. 建立 Value 節點進行運算（加、乘、冪次、對數、指數、ReLU 等）
2. 每個運算節點記錄其子節點與局部梯度

**反向傳播**:
1. 從輸出節點開始，DFS 建立拓樸排序
2. 設定輸出節點梯度為 1
3. 逆序遍歷，對每個節點的 child 傳遞梯度: `child.grad += local_grad * node.grad`

**Adam 參數更新**:
1. 更新一階動量 (m) 與二階動量 (v)
2. 計算偏差修正後的 m_hat 與 v_hat
3. 更新參數: `p -= lr * m_hat / (sqrt(v_hat) + eps)`

### 數學公式

**鏈式法則**:
$$\frac{\partial L}{\partial x} = \frac{\partial L}{\partial y} \cdot \frac{\partial y}{\partial x}$$

**加法節點**:
$$y = a + b,\quad \frac{\partial y}{\partial a} = 1,\quad \frac{\partial y}{\partial b} = 1$$

**乘法節點**:
$$y = a \times b,\quad \frac{\partial y}{\partial a} = b,\quad \frac{\partial y}{\partial b} = a$$

**ReLU 激活函數**:
$$ReLU(x) = \max(0, x),\quad \frac{\partial ReLU}{\partial x} = \begin{cases} 1 & x > 0 \\ 0 & x \leq 0 \end{cases}$$

**Softmax 函數**:
$$softmax(x_i) = \frac{e^{x_i - M}}{\sum_{j} e^{x_j - M}},\quad M = \max(x)$$

**RMSNorm**:
$$RMSNorm(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2 + \epsilon}}$$

### 使用場景

- 在 C 語言環境中實作神經網路
- 嵌入式系統中的機器學習
- 理解自動微分引擎的底層實作細節
- 高效能場景下避免 Python 的開銷

### 優缺點

| 優點 | 缺點 |
|------|------|
| 執行效率高，無 Python 直譯器開銷 | 缺乏動態語言的靈活性 |
| 記憶體管理可控（Arena 分配器） | 開發調試週期較長 |
| 完整實作自動微分與神經網路元件 | 無 GPU 加速支援 |
| 適合嵌入式和系統程式設計場景 | 記憶體安全需程式設計師自行管理 |
