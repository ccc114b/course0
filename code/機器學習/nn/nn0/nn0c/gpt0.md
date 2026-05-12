# GPT-0 — C 語言實作之迷你 GPT 語言模型

## 原理

GPT-0 是一個用 C 語言實作的簡化版 GPT（Generative Pre-trained Transformer）語言模型，建立在 nn0 自動微分引擎之上。它實作了 Token Embedding、位置編碼、多頭因果注意力（Causal Multi-Head Attention）、RMS 正規化、前饋神經網路（MLP）以及完整的訓練與推理流程。

### 核心架構

1. **Embedding 層**: 將離散 token ID 映射為連續向量（wte），加上位置編碼（wpe）
2. **多頭因果注意力**: 每個位置只能看到過去的位置（包含自身），透過 softmax 計算加權和
3. **前饋網路 (MLP)**: 兩層線性變換，中間使用 ReLU 激活，維度先擴張再壓縮
4. **殘差連接**: 每個子層的輸出與輸入相加，有助於梯度傳遞
5. **Pre-LN (Pre-Layer Normalization)**: 在每個子層之前做 RMSNorm
6. **KV Cache**: 推論時快取已計算的 Key 和 Value，避免重複計算

### 演算法步驟

**訓練階段**:
1. 初始化所有權重矩陣（常態分佈隨機初始化）
2. 對每個文檔進行字符級 tokenize
3. Forward: 輸入 embedding → N 層 Transformer → lm_head → logits
4. Softmax → 交叉熵損失
5. Backward: 反向傳播計算梯度
6. Adam 優化器更新參數
7. 重複直到收斂

**推論階段**:
1. 從 BOS token 開始，使用 KV Cache 逐 token 生成
2. 對每一步的 logits 應用 temperature scaling
3. Softmax 後依機率取樣下一個 token
4. 遇到 BOS 或達到最大長度時停止

### 數學公式

**Embedding + Position Encoding**:
$$x = W_{te}[token] + W_{pe}[pos]$$

**Scaled Dot-Product Attention**:
$$Attention(Q, K, V) = softmax\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

**Causal Mask**:
$$M_{ij} = \begin{cases} 0 & i \geq j \\ -\infty & i < j \end{cases}$$

**MLP**:
$$MLP(x) = W_{fc2} \cdot ReLU(W_{fc1} \cdot x)$$

**Residual Connection**:
$$x' = x + Sublayer(RMSNorm(x))$$

### 使用場景

- 小型文本生成任務（人名、簡單句子）
- 在 C 語言環境中示範 Transformer 架構
- 理解 GPT 語言模型的完整訓練流程
- 低資源環境的文字生成

### 優缺點

| 優點 | 缺點 |
|------|------|
| C 語言實作效率高，無額外執行環境開銷 | 標量級別的自動微分，訓練速度慢 |
| 完整展示 Transformer 訓練與推理 | 缺少批次處理（batch）支援 |
| 支援 UTF-8 字符集處理 | 模型規模小，生成能力有限 |
| 使用記憶體池管理，記憶體配置高效 | C 語言的記憶體管理較複雜 |
| 推論時使用 KV Cache 加速 | 缺少現代 Transformer 的許多改進（GELU、LayerNorm 等） |
