# CNN0 MNIST 訓練範例程式

## 原理

本範例展示如何使用 cnn0.py 的卷積神經網路在 MNIST 手寫數字資料集上進行訓練與測試。由於純 Python 自動微分引擎的效能限制，僅使用 1000 筆訓練資料與 50 筆測試資料。

### 核心流程

1. 載入 MNIST 資料集（自動下載）
2. 降採樣 28×28 影像為 14×14
3. CNN 模型：Conv2D(1→4, 3×3) → ReLU → MaxPool(2×2) → Linear(144→10)
4. Adam 優化器訓練 5 個 Epoch
5. 測試階段驗證準確率

### 數學公式

**CNN 架構**:
$$Input(1 \times 14 \times 14) \xrightarrow{Conv} 4 \times 12 \times 12 \xrightarrow{ReLU} 4 \times 12 \times 12 \xrightarrow{Pool} 4 \times 6 \times 6 \xrightarrow{Flatten} 144 \xrightarrow{Linear} 10$$

### 使用場景

- MNIST 手寫數字分類教學
- 展示 CNN 在影像分類中的應用
- 驗證自動微分引擎支援卷積運算

### 優缺點

| 優點 | 缺點 |
|------|------|
| 完整展示 CNN 訓練流程 | 純 Python 引擎訓練極慢 |
| 支援 MNIST 標準資料格式 | 僅支援極少樣本（1000 筆） |
| 自動下載資料集，開箱即用 | 降採樣可能遺失細節資訊 |
