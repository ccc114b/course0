# Actor-Critic 模型 (PPO) — Walker2d-v5

## 原理

此模型為 PPO (Proximal Policy Optimization) 演算法的核心組件，包含 Actor 與 Critic 兩個子網路：

1. **Actor 網路**：輸出動作的均值 $\mu$，搭配可學習的 $\log \sigma$ 參數形成高斯分布。輸出經過 Tanh 激活函數確保動作在 $[-1, 1]$ 範圍內。
2. **Critic 網路**：輸出狀態價值 $V(s)$，用於計算優勢函數。

此外包含一個 `RunningMeanStd` 類別，用於在訓練過程中即時計算狀態的均值與標準差，實現觀測歸一化。

## 演算法步驟

1. **初始化**：建立 256×256 的 Actor 與 Critic 網路，初始化 $\log \sigma = 0$
2. **動作選擇** (`get_action`)：
   - Actor 輸出均值 $\mu$，與 $\sigma = \exp(\log \sigma)$ 組成高斯分布
   - 從分布抽樣取得動作，計算對數機率
3. **評估** (`evaluate`)：
   - 對給定的 $(s, a)$ 計算對數機率、價值估計與熵

## 數學公式

**高斯策略**:
$$\pi(a|s) = \mathcal{N}(a; \mu_\theta(s), \sigma^2), \quad \sigma = \exp(\log \sigma)$$

**狀態價值估計**:
$$V_\phi(s) = \text{Critic}_\phi(s)$$

## 使用場景

- 連續動作空間的 MuJoCo 控制任務
- 搭配 PPO 演算法進行穩定訓練
- 需要狀態歸一化的強化學習任務

## 優缺點

| 優點 | 缺點 |
|------|------|
| 可學習的 $\log \sigma$ 適應不同動作維度 | 無法處理多元動作分布（只支援高斯） |
| Tanh 輸出確保動作範圍 | 網路規模固定，不自動調整 |
| RunningMeanStd 實現線上歸一化 | $\log \sigma$ 共享於所有狀態 |
