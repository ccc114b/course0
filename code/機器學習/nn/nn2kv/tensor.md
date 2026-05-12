# Tensor — Python 自動微分張量引擎（nn2kv 版）

## 原理

與 nn1tensor 的 Tensor 引擎相同，但新增了 `cat` 函數支援張量拼接。此功能為 KV Cache 實作所必需，允許在推論時將過去的 Key/Value 與當前步驟的 Key/Value 沿序列維度拼接。

### 新增功能

**cat (拼接)**:
- 沿指定維度拼接多個 Tensor
- 反向傳播時將梯度沿拼接維度切分後分配給原始張量

### 數學公式

**cat 反向傳播**:
若 $C = concat(A, B, axis=d)$ 且 shape 分別為 $[s_1, ..., s_d^A, ...]$ 與 $[s_1, ..., s_d^B, ...]$，則：
$$\frac{\partial L}{\partial A} = \frac{\partial L}{\partial C}[:, ..., :s_d^A, ...]$$
$$\frac{\partial L}{\partial B} = \frac{\partial L}{\partial C}[:, ..., s_d^A:, ...]$$

### 使用場景

- KV Cache 的 Key/Value 拼接
- 需要動態擴展序列維度的情境
- 推論時逐步累積注意力快取

### 優缺點

| 優點 | 缺點 |
|------|------|
| 支援動態拼接序列 | 每次拼接會增加計算圖深度 |
| 反向傳播正確處理梯度分配 | 長時間序列可能造成記憶體膨脹 |
| 與現有 Tensor API 完全相容 | 尚無 in-place 優化 |
