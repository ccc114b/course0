# gpt0.rs — Rust GPT 語言模型實作

## 原理

gpt0.rs 是以 Rust 實作的簡化版 GPT 語言模型，基於 nn0.rs 自動微分引擎。包含 Token Embedding、位置編碼、多頭因果注意力、RMSNorm、MLP 等完整 Transformer 元件，支援訓練與自回歸文本生成。

### 核心架構

1. **Gpt 結構體**: 儲存模型超參數、權重字典與攤平參數列表
2. **LanguageModel Trait**: 定義模型介面（block_size, n_layer, forward）
3. **train 函數**: 訓練迴圈
4. **inference 函數**: 自回歸文字生成

### 演算法步驟

**前向傳播**:
1. Token Embedding + Position Embedding 聯合編碼
2. RMSNorm → 對每層 Transformer：
   - 多頭注意力（Scaled Dot-Product Attention）
   - 殘差連接
   - MLP（FC1 → ReLU → FC2）
   - 殘差連接
3. lm_head 輸出 logits

**推論**:
1. 從 BOS 開始，逐 token 生成
2. 使用 KV Cache 儲存每層的 K/V 向量（展平為一維陣列）
3. Temperature scaling + Softmax → 加權取樣

### 數學公式

**KV Cache 儲存**:
$$K_{cache}[layer] = [K_0, K_1, ..., K_{t-1}, K_t]$$
$$V_{cache}[layer] = [V_0, V_1, ..., V_{t-1}, V_t]$$

**從快取中取出第 t 個時間點的 K**:
$$K_t = K_{cache}[t \cdot n_{embd} : t \cdot n_{embd} + n_{embd}]$$

### 使用場景

- Rust 環境的文本生成
- 理解 Transformer 在 Rust 中的實作方式
- 高效能語言模型推論

### 優缺點

| 優點 | 缺點 |
|------|------|
| Rust 型別系統保證記憶體安全 | 實作較 Python 版本冗長 |
| 使用 Rc<RefCell<>> 實作自動微分 | 仍需標量級別運算，效率受限 |
| KV Cache 實作清晰 | 缺少批次與 GPU 支援 |
