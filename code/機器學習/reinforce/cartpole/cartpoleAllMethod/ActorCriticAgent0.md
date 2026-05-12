# Actor-Critic (簡化版) — CartPole-v1

## 原理

此實作為 Actor-Critic 方法的簡化版本，與標準 Actor-Critic 不同之處在於優勢函數的計算方式：直接使用折扣回報與當前價值估計的差值作為優勢值，而非使用 TD 誤差。

$$A_t = G_t - V(s_t)$$

這種方式雖然直觀，但 $G_t$ 本身是由完整軌跡計算而來（Monte Carlo 性質），因此仍帶有較高的方差。不過由於 Critic 提供了基線 $V(s_t)$，方差仍比純 VPG 低。

## 演算法步驟

1. 初始化 Actor 網路 $\pi_\theta$ 與 Critic 網路 $V_\phi$
2. 對每個回合：
   - 收集軌跡（含 Critic 估算的價值）
   - 回合結束後：
     a. 計算折扣回報 $G_t = \sum_{k=t}^{T} \gamma^{k-t} r_k$
     b. 計算優勢 $A_t = G_t - V(s_t)$
     c. **更新 Actor**：沿 $-\frac{1}{T}\sum A_t \log \pi(a_t|s_t)$ 梯度下降
     d. **更新 Critic**：沿 $\frac{1}{T}\sum (G_t - V(s_t))^2$ 梯度下降

## 數學公式

**Actor 損失**:
$$\mathcal{L}_{\text{actor}} = -\frac{1}{T}\sum_{t=0}^{T} (G_t - V_\phi(s_t)) \log \pi_\theta(a_t|s_t)$$

**Critic 損失**:
$$\mathcal{L}_{\text{critic}} = \frac{1}{T}\sum_{t=0}^{T} (V_\phi(s_t) - G_t)^2$$

## 使用場景

- Actor-Critic 方法的入門教學
- 理解基線（Baseline）對策略梯度的影響
- 與標準 Actor-Critic（使用 TD 誤差）進行比較

## 優缺點

| 優點 | 缺點 |
|------|------|
| 加入基線降低方差 | $G_t$ 仍為 Monte Carlo 估計，方差較大 |
| 概念直觀易理解 | 需完整回合才能更新 |
| 比 VPG 更穩定 | Critic 估計不準時會影響 Actor |
