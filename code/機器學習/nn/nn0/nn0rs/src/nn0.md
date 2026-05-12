# nn0.rs — Rust 自動微分引擎與神經網路元件

## 原理

nn0.rs 是以 Rust 實作的自動微分引擎與神經網路基礎元件庫。使用 `Rc<RefCell<>>` 模式實作共享所有權與內部可變性的計算圖節點，支援反向傳播計算梯度。包含 Adam 優化器、線性層、Softmax、RMSNorm、交叉熵損失等完整元件。

### 核心架構

1. **ValueInner 結構體**: 節點內部狀態（data, grad, children, local_grads）
2. **ValueRef**: 透過 `Rc<RefCell<ValueInner>>` 提供共享可變引用
3. **Adam 優化器**: Rust 實作的自適應學習率演算法
4. **LanguageModel Trait**: 語言模型泛型介面
5. **單元測試**: 完整的基本運算、Softmax、RMSNorm、Adam、交叉熵測試

### 演算法步驟

**反向傳播（Rust 注意事項）**:
1. DFS 拓樸排序（使用 HashSet 追蹤已訪問節點）
2. 設定輸出節點梯度 = 1
3. 逆序遍歷：
   - 先將節點的 children 與 local_grads clone 出來
   - 釋放 borrow 後再修改子節點的 grad（避免借用衝突）

**Adam 更新**:
1. 更新 m, v 動量
2. 偏差修正
3. 參數更新後清除梯度

### 數學公式

**鏈式法則（Rust 實作注意事項）**:
$$\frac{\partial L}{\partial child} += \frac{\partial output}{\partial child} \times \frac{\partial L}{\partial output}$$

### 使用場景

- Rust 專案中的自動微分需求
- 系統程式設計語言的神經網路實作
- 理解 Rust 所有權模型在 ML 中的應用

### 優缺點

| 優點 | 缺點 |
|------|------|
| Rust 記憶體安全保證 | Rc<RefCell<>> 增加執行時開銷 |
| 完整的單元測試覆蓋 | 借用檢查器增加實作複雜度 |
| 型別系統提供更好的編譯期檢查 | 無 GPU 加速支援 |
| 學習 Rust 所有權/借用模型的好案例 | API 較動態語言繁瑣 |
