# GPT — 基於 Tensor 引擎的 GPT 語言模型

## 原理

此模組實作了基於 Tensor 自動微分引擎的 GPT 語言模型，包含因果自注意力（Causal Self-Attention）、多層感知器（MLP）、Transformer Block 以及完整的 GPT 模型。所有運算皆支援批次向量化。

### 核心架構

1. **CausalSelfAttention**: 因果多頭注意力（含遮蔽未來）
2. **MLP**: 前饋神經網路（FC1 → ReLU → FC2）
3. **Block**: 完整的 Transformer 層（Attention + MLP + 殘差連接 + Pre-LN）
4. **GPT**: 完整語言模型（Embedding → N 層 Block → LN → lm_head）

### 演算法步驟

1. Token Embedding + Position Embedding
2. 對每層 Block：
   - Pre-LN → Causal Self-Attention → 殘差連接
   - Pre-LN → MLP → 殘差連接
3. Final LayerNorm → lm_head

### 數學公式

**Causal Self-Attention**:
$$Q = xW_Q,\; K = xW_K,\; V = xW_V$$
$$Attention(Q, K, V) = softmax\left(\frac{QK^T}{\sqrt{d_k}} + M\right)V$$
$$M_{ij} = \begin{cases} 0 & i \geq j \\ -\infty & i < j \end{cases}$$

**GPT 網路結構**:
$$h_0 = W_{te}[idx] + W_{pe}[pos]$$
$$h_l = Block_l(h_{l-1}),\; l \in [1, L]$$
$$logits = h_L \cdot W_{lm\_head}^T$$

### 使用場景

- 基於 Tensor 引擎的語言模型訓練
- 向量化批次文字生成
- 理解 GPT 模型的 Tensor 實現

### 優缺點

| 優點 | 缺點 |
|------|------|
| 向量化運算，支援批次 | 無 KV Cache，推論效率低 |
| 完整的 Causal Mask 實作 | 矩陣乘法計算圖複雜 |
| 簡潔的 Block 組合設計 | 反向傳播記憶體佔用高 |
