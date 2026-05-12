# VPG (Vanilla Policy Gradient / REINFORCE) — CartPole-v1

## 原理

VPG 是最基礎的策略梯度演算法，直接對策略進行參數化，使用 Monte Carlo 估計的折扣回報 $G_t$ 作為權重來更新策略網路。其核心公式來自策略梯度定理：

$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau}\left[\sum_{t=0}^{T} G_t \nabla_\theta \log \pi_\theta(a_t|s_t)\right]$$

此實作使用 softmax 輸出層的單層線性網路（無隱藏層）作為策略網路，適用於 CartPole 的簡單狀態空間。

## 演算法步驟

1. 初始化策略網路 $\pi_\theta$（Softmax 輸出）
2. 對每個回合：
   - 使用當前策略收集完整軌跡 $(s_t, a_t, r_t)$
3. 回合結束後：
   a. 計算折扣回報 $G_t = \sum_{k=t}^{T} \gamma^{k-t} r_k$
   b. 計算每個狀態的動作機率 $\pi(a_t|s_t)$
   c. 計算損失 $\mathcal{L} = -\frac{1}{T}\sum_t G_t \log \pi(a_t|s_t)$
   d. 梯度下降更新策略參數

## 數學公式

**折扣回報**:
$$G_t = \sum_{k=t}^{T} \gamma^{k-t} r_k$$

**策略梯度損失**:
$$\mathcal{L}(\theta) = -\frac{1}{T}\sum_{t=0}^{T} G_t \log \pi_\theta(a_t|s_t)$$

## 使用場景

- 強化學習入門教學
- 策略梯度方法的比較基線
- 簡單控制任務（如 CartPole）

## 優缺點

| 優點 | 缺點 |
|------|------|
| 實現簡單直接 | 樣本效率低（需完整回合） |
| 直接優化目標策略 | 梯度方差大，收斂不穩定 |
| 不收斂到局部 Q 值 | 對學習率非常敏感 |
