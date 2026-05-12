# nn.py — 神經網路模組層（nn2kv 版）

## 原理

與 nn1tensor 版的 nn.py 功能相同，包含 Module 基類、Linear、Embedding、RMSNorm 與 Adam 優化器。此版本被 nn2kv 的 GPT 模型使用。

### 核心元件

1. **Module**: 基底類別，遞迴收集參數
2. **Linear**: 全連接層
3. **Embedding**: 查表嵌入層
4. **RMSNorm**: 根均方正規化
5. **Adam**: 向量化 Adam 優化器

其數學原理與 nn1tensor 版完全相同。

### 使用場景

- nn2kv GPT 模型的基礎元件
- 批次神經網路訓練
- 向量化自動微分

### 優缺點

同 nn1tensor 版。
