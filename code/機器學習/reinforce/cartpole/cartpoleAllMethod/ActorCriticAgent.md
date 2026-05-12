# Actor-Critic — CartPole-v1

## 原理

Actor-Critic 方法結合了策略梯度（Actor）與價值函數（Critic）兩種強化學習範式。Actor 負責學習策略 $\pi_\theta(a|s)$，Critic 負責估計狀態價值 $V_\phi(s)$，Critic 的估計值作為基線來降低 Actor 更新的方差。

此實作使用**優勢函數（Advantage Function）** 來更新 Actor，其中優勢定義為 TD 誤差：
$$A_t = r_t + \gamma V(s_{t+1}) - V(s_t)$$

優勢函數衡量當前動作相對於平均表現的好壞，這比直接用折扣回報 $G_t$ 更加穩定。

## 演算法步驟

1. 初始化 Actor 網路 $\pi_\theta$ 與 Critic 網路 $V_\phi$
2. 對每個回合：
   - 使用 Actor 選擇動作，記錄軌跡（含 Critic 的價值估計）
   - 回合結束後：
     a. 計算折扣回報 $G_t$
     b. 計算優勢 $A_t = r_t + \gamma V(s_{t+1}) - V(s_t)$
     c. **更新 Actor**：$\mathcal{L}_{\text{actor}} = -\frac{1}{T}\sum_t A_t \log \pi_\theta(a_t|s_t)$
     d. **更新 Critic**：$\mathcal{L}_{\text{critic}} = \frac{1}{T}\sum_t (V_\phi(s_t) - G_t)^2$

## 數學公式

**Actor 損失**:
$$\mathcal{L}_{\text{actor}} = -\frac{1}{T}\sum_{t=0}^{T} A_t \log \pi_\theta(a_t|s_t)$$

**優勢函數**:
$$A_t = r_t + \gamma V_\phi(s_{t+1}) - V_\phi(s_t)$$

**Critic 損失**:
$$\mathcal{L}_{\text{critic}} = \frac{1}{T}\sum_{t=0}^{T} (V_\phi(s_t) - G_t)^2$$

## 使用場景

- 需要降低策略梯度方差的情境
- 相比 VPG 需要更穩定收斂的任務
- 可同時輸出策略與價值估計的應用

## 優缺點

| 優點 | 缺點 |
|------|------|
| 方差比 VPG 更小，訓練更穩定 | 需要同時維護兩個網路 |
| 可進行單步更新（不需完整回合） | Critic 的估計偏差會影響 Actor |
| 結合了 Policy-based 與 Value-based 的優點 | 超參數更多（兩個學習率） |
