# chargpt.py — 字符級 GPT 訓練與推論函數

## 原理

此模組封裝了 GPT 模型的訓練與推論流程，提供 `train_model` 與 `generate_samples` 兩個高階函數。訓練時不使用 KV Cache（直接計算整段序列），推論時使用 KV Cache 加速。

### 核心功能

1. **train_model**: 訓練函數，含梯度裁剪（Gradient Clipping）防止梯度爆炸
2. **generate_samples**: 推論函數，使用 KV Cache 搭載閃電加速

### 演算法步驟

**訓練**:
1. 每個 step tokenize 一個文檔
2. 前向傳播（不用 KV Cache）
3. Cross-Entropy Loss
4. 反向傳播
5. 梯度裁剪（max_norm=1.0）
6. Adam 更新 + 學習率衰減

**推論**:
1. 每個樣本從 BOS 開始
2. 使用 KV Cache 逐 token 生成
3. 每次輸入僅為當前 token（長度 1），快取包含完整歷史

### 數學公式

**梯度裁剪**:
$$g = g \cdot \min\left(1, \frac{max\_norm}{\|g\| + \epsilon}\right)$$

### 使用場景

- 字符級語言模型訓練與推論的高階 API
- 需要梯度裁剪穩定訓練的場景
- 展示 KV Cache 推論加速

### 優缺點

| 優點 | 缺點 |
|------|------|
| 高階 API，易於使用 | 批次大小固定為 1 |
| 梯度裁剪提高訓練穩定性 | 梯度裁剪增加計算開銷 |
| KV Cache 加速推論 | 長時間生成時 Cache 記憶體持續增長 |
