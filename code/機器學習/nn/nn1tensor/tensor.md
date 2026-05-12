# Tensor — Python 自動微分張量引擎

## 原理

Tensor 類別實作了基於 NumPy 的自動微分張量引擎。它追蹤所有張量運算並建構計算圖，支援反向傳播計算梯度。此引擎是 nn1tensor 系列（從標量 Value 升級為向量化 Tensor）的核心基礎。

### 核心功能

1. **自動微分**: 支援加法、乘法、矩陣乘法、轉置、reshape 等運算的反向傳播
2. **激活函數**: ReLU、Softmax（含數值穩定處理）
3. **損失函數**: Cross-Entropy（融合 Softmax 提高穩定性）
4. **廣播處理**: `unbroadcast` 函數處理 NumPy 廣播機制的梯度還原

### 演算法步驟

**前向傳播**:
1. 建立 Tensor 節點儲存資料與依賴關係
2. 記錄 `_backward` 閉包，包含反向傳播所需邏輯

**反向傳播**:
1. 對計算圖進行拓樸排序
2. 設定輸出節點梯度為全 1 矩陣
3. 逆序執行每個節點的 `_backward` 函數

### 數學公式

**Softmax 反向傳播**（Jacobian-vector product）:
$$\frac{\partial L}{\partial x_i} = s_i \left(\frac{\partial L}{\partial s_i} - \sum_j \frac{\partial L}{\partial s_j} s_j\right)$$

**Cross-Entropy 反向傳播**:
$$\frac{\partial L}{\partial logits_i} = p_i - 1_{i = target}$$

**矩陣乘法反向傳播**:
$$\frac{\partial L}{\partial X} = \frac{\partial L}{\partial Y} \cdot W^T, \quad \frac{\partial L}{\partial W} = X^T \cdot \frac{\partial L}{\partial Y}$$

### 使用場景

- 神經網路的向量化實作（拋棄標量 Value）
- 需要高效張量運算的自動微分場景
- 教學用：理解從標量到張量的自動微分演進

### 優缺點

| 優點 | 缺點 |
|------|------|
| 向量化運算，效能遠超標量 Value | 部分反向傳播實作有 for 迴圈（cross_entropy） |
| 基於 NumPy，生態系豐富 | 無 GPU 支援 |
| 支援廣播機制 | 部分鏈式求導實作較複雜 |
