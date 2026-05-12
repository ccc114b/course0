# VPG with Baseline (Vanilla Policy Gradient + Baseline) — CartPole-v1

## 原理

帶基線的 VPG 在原始 REINFORCE 演算法的基礎上引入一個基線函數 $b(s)$（通常為狀態價值函數 $V(s)$），以降低策略梯度更新的方差。基線的作用是提供一個參照點：若折扣回報高於基線則提升該動作的機率，反之則降低。

基線 $V_\phi(s)$ 透過最小化與折扣回報 $G_t$ 的均方誤差來學習。更新時，使用 $G_t - V(s_t)$ 作為策略梯度的權重。

此實作進一步引入了折扣回報的歸一化處理，並將 $\gamma^t$ 因子明確納入優勢計算中。

## 演算法步驟

1. 初始化策略網路 $\pi_\theta$ 與基線網路 $V_\phi$
2. 對每個回合：
   - 收集完整軌跡
3. 回合結束後：
   a. 計算折扣回報 $G_t = \sum_{k=t}^{T} \gamma^{k-t} r_k$
   b. **更新基線**：最小化 $(V_\phi(s_t) - G_t/\gamma^t)^2$
   c. 計算優勢 $\psi_t = G_t - \gamma^t V_\phi(s_t)$
   d. **更新策略**：$\mathcal{L}_{\text{policy}} = -\frac{1}{T}\sum_t \psi_t \log \pi_\theta(a_t|s_t)$

## 數學公式

**折扣回報**:
$$G_t = \sum_{k=t}^{T} \gamma^{k-t} r_k$$

**基線損失**:
$$\mathcal{L}_{\text{baseline}} = \frac{1}{T}\sum_{t=0}^{T} \left(V_\phi(s_t) - \frac{G_t}{\gamma^t}\right)^2$$

**策略梯度損失**:
$$\mathcal{L}_{\text{policy}} = -\frac{1}{T}\sum_{t=0}^{T} \psi_t \log \pi_\theta(a_t|s_t)$$
$$\psi_t = G_t - \gamma^t V_\phi(s_t)$$

## 使用場景

- 需要降低策略梯度方差的任務
- 標準 VPG 收斂不穩定的情況
- 理解基線對策略梯度影響的教學範例

## 優缺點

| 優點 | 缺點 |
|------|------|
| 基線有效降低梯度方差 | 需要訓練額外的基線網路 |
| 比純 VPG 收斂更穩定 | 基線估計偏差會影響策略更新 |
| 易於實作與理解 | 超參數更多 |
