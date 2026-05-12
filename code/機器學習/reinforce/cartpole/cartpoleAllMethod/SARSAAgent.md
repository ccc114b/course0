# SARSA (State-Action-Reward-State-Action) — CartPole-v1

## 原理

SARSA 是一種基於策略（On-policy）的 TD 學習演算法。與 Q-learning 不同，SARSA 在更新時使用的是實際執行的下一步動作 $a'$，而非貪婪的最大 Q 值動作。因此 SARSA 學習的是當前行為策略下的 Q 函數，而非最優策略的 Q 函數。

此實作使用深度神經網路逼近 Q 函數，並結合經驗回放（Experience Replay）進行批次訓練。由於 SARSA 是基於策略的方法，使用經驗回放需要特別注意 — 回放中的轉移 $(s, a, r, s', a')$ 必須由同一策略產生。

## 演算法步驟

1. 初始化 Q 網路 $Q(s,a;\theta)$
2. 對每個時間步：
   - 以 $\epsilon$-greedy 策略選擇動作 $a$
   - 執行動作 $a$，觀察 $(r, s')$
   - 以 $\epsilon$-greedy 策略選擇下一步動作 $a'$（在 $s'$ 狀態下）
   - 將轉移 $(s, a, r, s', a')$ 存入回放緩衝區
   - 當緩衝區樣本足夠後：
     a. 抽樣一個批次
     b. 計算 TD 目標：$y = r + \gamma Q(s', a'; \theta)$
     c. 計算損失：$\mathcal{L} = (y - Q(s,a;\theta))^2$
     d. 梯度下降更新 Q 網路

## 數學公式

**SARSA 更新目標**:
$$y_i = r_i + \gamma Q(s_i', a_i'; \theta)$$

**損失函數**:
$$\mathcal{L}(\theta) = \frac{1}{N}\sum_{i=1}^{N} \left(y_i - Q(s_i, a_i; \theta)\right)^2$$

## 使用場景

- 需要在學習過程中考慮安全性的任務
- 與 Q-learning 進行比較研究
- 行為策略本身也需要學習的情境

## 優缺點

| 優點 | 缺點 |
|------|------|
| 考慮實際行動，在危險環境更安全 | 基於策略學習，樣本效率較低 |
| 對雜訊獎勵較魯棒 | 使用回放緩衝區有理論不一致性 |
| 比 Q-learning 更保守、更穩定 | 學習速度通常比 Q-learning 慢 |
