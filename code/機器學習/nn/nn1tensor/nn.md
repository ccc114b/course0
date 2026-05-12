# nn.py — 神經網路模組層（nn1tensor 版）

## 原理

此模組在 Tensor 自動微分引擎之上實作了神經網路的常見元件：Module 基類、Linear 全連接層、Embedding 層、RMSNorm 正規化層以及 Adam 優化器。所有層皆支援 Tensor 的批次輸入。

### 核心架構

1. **Module**: 基底類別，提供 `parameters()` 遞迴收集所有可訓練參數
2. **Linear**: 全連接層 $y = xW + b$
3. **Embedding**: 查表嵌入層，從權重矩陣中取出對應索引的向量
4. **RMSNorm**: 根均方正規化
5. **Adam**: 基於 Tensor 的向量化 Adam 優化器

### 數學公式

**Embedding 反向傳播**:
$$\frac{\partial L}{\partial W[idx]} += \frac{\partial L}{\partial out}$$

使用 `np.add.at` 處理索引重複的情況。

**RMSNorm 反向傳播**:
$$\frac{\partial L}{\partial x} = \frac{\partial L}{\partial y} \cdot \frac{1}{\sqrt{ms}} - \frac{x \cdot \frac{1}{\sqrt{ms}^3} \cdot \sum(\frac{\partial L}{\partial y} \cdot x)}{n}$$

### 使用場景

- 建構基於 Tensor 的神經網路
- 批次訓練的神經網路層
- 理解 Module 的參數管理機制

### 優缺點

| 優點 | 缺點 |
|------|------|
| 支援批次輸入，效能較 Value 版大幅提升 | 手動實作反向傳播公式，容易出錯 |
| Module 自動收集參數 | Embedding 的 `.data` 直接索引可能斷開計算圖 |
| 簡潔的 Layer API 設計 | 無正規化層的增益參數 (gamma) |
