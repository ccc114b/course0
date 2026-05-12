# VPG (Vanilla Policy Gradient) — CartPole-v1

## 原理

VPG（又稱 REINFORCE）是策略梯度方法中最基礎的演算法。其核心思想是直接對策略 $\pi_\theta(a|s)$ 進行參數化，並沿著最大化期望累積報酬的方向調整策略參數。

與基於價值的 Q-learning 不同，VPG 不學習狀態-動作價值函數，而是直接優化策略網路。它使用 Monte Carlo 方法計算整個回合的折扣回報 $G_t$，並以 $G_t$ 作為權重來更新策略，提升好的行動出現機率、降低不好的行動出現機率。

## 演算法步驟

1. 初始化策略網路 $\pi_\theta$（Softmax 輸出層）
2. 對每個回合：
   - 使用當前策略與環境互動，記錄完整軌跡 $(s_0, a_0, r_1, s_1, ..., s_{T-1}, a_{T-1}, r_T)$
3. 回合結束後：
   - 計算每個時間步的折扣回報 $G_t = \sum_{k=t}^{T} \gamma^{k-t} r_k$
   - 計算策略損失 $\mathcal{L} = -\frac{1}{T} \sum_t G_t \log \pi_\theta(a_t|s_t)$
   - 反向傳播更新策略參數
4. 重複直到收斂

## 數學公式

**策略梯度定理**:
$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\left[\sum_{t=0}^{T} G_t \nabla_\theta \log \pi_\theta(a_t|s_t)\right]$$

**折扣回報**:
$$G_t = \sum_{k=t}^{T} \gamma^{k-t} r_k$$

**損失函數**:
$$\mathcal{L}(\theta) = -\frac{1}{T}\sum_{t=0}^{T} G_t \log \pi_\theta(a_t|s_t)$$

## 使用場景

- 離散動作空間的強化學習問題
- 簡單的控制任務（如 CartPole）
- 作為理解更高階策略梯度方法的起點

## 優缺點

| 優點 | 缺點 |
|------|------|
| 概念簡單，容易實作 | 樣本效率低（需完整回合才能更新） |
| 可處理隨機策略 | 梯度方差大，收斂不穩定 |
| 直接優化目標函數 | 對學習率敏感 |
| 不需要值函數估計 | 不適合長回合任務 |
