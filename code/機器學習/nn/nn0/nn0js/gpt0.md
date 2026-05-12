# gpt0.js — JavaScript GPT 語言模型實作

## 原理

gpt0.js 是以 JavaScript 實作的迷你 GPT 語言模型，基於 nn0.js 自動微分引擎。包含 Embedding 層、多頭因果注意力、RMSNorm、MLP 等完整 Transformer 元件，支援訓練與自回歸文本生成。

### 核心架構

1. **Gpt 類別**: GPT 模型主體，包含初始化、前向傳播
2. **train 函數**: 訓練迴圈，對每個文檔執行一步梯度下降
3. **inference 函數**: 自回歸文字生成
4. **KV Cache**: 推論時快取已計算的 K/V 向量加速生成

### 演算法步驟

**前向傳播**:
1. Token Embedding + Position Embedding → 聯合編碼
2. RMSNorm → Multi-Head Attention (含因果遮蔽)
3. 殘差連接 → RMSNorm → MLP (FC1 → ReLU → FC2)
4. 殘差連接 → lm_head → logits

**訓練**:
1. Tokenize → 嵌入 → N 層 Transformer → lm_head
2. Softmax → Cross-Entropy Loss
3. 反向傳播 → Adam 更新

**推論**:
1. 從 BOS 開始，逐 token 生成
2. 每一步更新 KV Cache，避免重算歷史

### 數學公式

**Attention with KV Cache**:
$$Attention(Q, K_{all}, V_{all}) = softmax\left(\frac{Q[K_{past}; K_{current}]^T}{\sqrt{d_k}}\right)[V_{past}; V_{current}]$$

### 使用場景

- Node.js 環境的文本生成應用
- JavaScript 全端 ML 教學範例
- 小型語言模型實驗

### 優缺點

| 優點 | 缺點 |
|------|------|
| 純 JS 實作，無需編譯 | 純標量運算，訓練極慢 |
| 完整展示 GPT 架構 | 無批次支援 |
| 推論支援 KV Cache | 模型容量小，生成品質有限 |
