# MicroGPT — 從零實現的迷你 GPT 語言模型

## 原理

MicroGPT 是一個純 Python、無外部依賴的迷你 GPT（Generative Pre-trained Transformer）語言模型實作。它包含完整的自動微分引擎、多頭注意力機制、RMS 正規化、Adam 優化器以及字符級的分詞器。整個訓練與推理流程在一個檔案中完成，展示了 Transformer 語言模型的核心運作原理。

### 核心架構

1. **自動微分引擎 (Value)**: 實作計算圖與反向傳播，支援加法、乘法、冪次、對數、指數、ReLU 等運算
2. **Token Embedding + Position Embedding**: 將離散的 token ID 映射為連續向量，並加上位置編碼
3. **多頭注意力 (Multi-Head Attention)**: 計算序列中各位置間的注意力權重，捕捉上下文關係
4. **前饋網路 (MLP)**: 每個位置的向量獨立經過兩層線性變換與 ReLU 激活
5. **RMS 正規化**: 取代 LayerNorm，簡化計算
6. **Adam 優化器**: 自適應學習率的最佳化演算法

### 演算法步驟

**訓練階段**:
1. 載入資料集（人名列表），建立字符集詞彙表
2. 對每個文檔進行 tokenize（字符轉 ID），前後加上 BOS 標記
3. 對序列中每個位置：
   - 前向傳播計算 logits
   - Softmax 轉為機率
   - 計算交叉熵損失
4. 反向傳播計算梯度
5. Adam 優化器更新參數
6. 重複直到收斂

**推理階段**:
1. 從 BOS token 開始
2. 前向傳播得到下一個 token 的機率分布
3. 依機率加權隨機取樣下一個 token
4. 若取到 BOS 則停止，否則重複

### 數學公式

**Scaled Dot-Product Attention**:
$$Attention(Q, K, V) = softmax\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

**多頭注意力**:
$$MultiHead(Q, K, V) = Concat(head_1, \dots, head_h)W_O$$
$$head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)$$

**RMS 正規化**:
$$RMSNorm(x) = \frac{x}{\sqrt{\frac{1}{n}\sum_{i=1}^n x_i^2 + \epsilon}}$$

**交叉熵損失**:
$$Loss = -\frac{1}{N}\sum_{i=1}^N \log P(x_{i+1} | x_1, \dots, x_i)$$

**Adam 更新規則**:
$$m_t = \beta_1 m_{t-1} + (1 - \beta_1) g_t$$
$$v_t = \beta_2 v_{t-1} + (1 - \beta_2) g_t^2$$
$$\hat{m}_t = \frac{m_t}{1 - \beta_1^t}, \quad \hat{v}_t = \frac{v_t}{1 - \beta_2^t}$$
$$\theta_t = \theta_{t-1} - \eta \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon}$$

### 使用場景

- 小型文本生成（人名、詩句、歌詞）
- Transformer 架構教學與學習
- 語言模型運作原理的完整示範
- 在資源受限的環境中實驗 NLP 任務

### 優缺點

| 優點 | 缺點 |
|------|------|
| 完全無外部依賴，僅用純 Python | 標量級別的自動微分效率極低 |
| 完整展示了 GPT 的核心概念 | 僅支援字符級分詞，無法處理子詞 |
| 程式碼簡潔（200 行），易於理解 | 模型極小（參數量不足），生成品質有限 |
| 同時包含訓練與推理 | 無批次處理，每次只處理一個樣本 |
| 使用 KV Cache 加速推論 | 無梯度裁剪等訓練穩定技巧 |
