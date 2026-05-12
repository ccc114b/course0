# GPT — 基於 Tensor 引擎的 GPT 語言模型（nn2kv KV Cache 版）

## 原理

此模組在 nn1tensor GPT 的基礎上加入了 KV Cache 支援。在推論時，快取每層的 Key 與 Value 張量，避免重複計算已處理過的 token，大幅提升自回歸生成的速度。

### 核心改進

1. **CausalSelfAttention**: 支援 KV Cache，在推論時拼接快取與當前 K/V
2. **Block**: 傳遞 KV Cache 給注意力層
3. **GPT**: 管理各層的 KV Cache，計算位置偏移

### 演算法步驟（推論）

1. 初始狀態：KV Cache 為 None
2. 輸入當前 token：
   - 計算當前位置的 K、V
   - 若 Cache 存在，拼接過去與當前的 K、V
   - 使用完整 K、V 計算注意力
   - 回傳更新後的 Cache
3. 每個新 token 只需前向傳播一次（而非從頭計算整個序列）

### 數學公式

**KV Cache 拼接**:
$$K_{all} = [K_{past}, K_{current}], \quad V_{all} = [V_{past}, V_{current}]$$

**位置偏移**:
$$pos_i = past\_len + i$$

### 使用場景

- 高效自回歸文字生成
- 需要快速推論的生產環境
- 比較有無 KV Cache 的效能差異

### 優缺點

| 優點 | 缺點 |
|------|------|
| 推論速度大幅提升（O(T) → O(1) 每步） | Cache 佔用記憶體 |
| 訓練時可選擇不使用 Cache | 實作略複雜 |
| 支援任意長度生成 | cache 張量拼接增加計算圖深度 |
