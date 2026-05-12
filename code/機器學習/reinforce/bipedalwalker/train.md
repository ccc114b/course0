# SAC (Soft Actor-Critic) — BipedalWalker-v3

## 原理

SAC (Soft Actor-Critic) 是一種基於最大熵框架的離策略強化學習演算法。與傳統 Actor-Critic 方法不同，SAC 在最大化累積報酬的同時也最大化策略的熵，這使得智能體在訓練過程中能夠維持探索的多樣性，避免過早收斂到局部最優解。

核心思想包含三個學習組件：
- **Actor (GaussianActor)**：輸出高斯分布的均值與對數標準差，透過重參數化技巧進行抽樣
- **Twin Critic (雙 Q 網路)**：使用兩個獨立的 Q 網路來減輕 Q 值高估偏差
- **自動熵溫度調整**：可選的自動調整機制，讓 $\alpha$ 在訓練中動態適應

## 演算法步驟

1. 初始化 Actor、兩個 Critic 網路、目標 Critic 網路、經驗回放緩衝區
2. 對每個時間步：
   - 在學習開始前使用隨機動作探索，之後使用 Actor 選擇動作
   - 儲存轉移 (s, a, r, s', done) 到回放緩衝區
   - 當緩衝區樣本足夠時進行更新：
     a. 從回放緩衝區隨機抽樣一個批次
     b. **更新 Critic**：使用目標網路計算 $Q_{\text{target}}$，最小化 MSE 損失
     c. **更新 Actor**：最大化 $Q(s, \tilde{a}) - \alpha \log \pi(\tilde{a}|s)$
     d. **更新 $\alpha$**（若啟用自動調整）：最小化 $\alpha(-\log\pi - \mathcal{H}_{\text{target}})$
     e. **軟更新**目標 Critic 網路參數
3. 定期記錄訓練統計與保存檢查點

## 數學公式

**Critic 損失**:
$$\mathcal{L}_Q = \mathbb{E}_{(s,a,r,s')\sim\mathcal{D}}\left[(Q_1(s,a) - y)^2 + (Q_2(s,a) - y)^2\right]$$
$$y = r + \gamma \left(\min_{i=1,2} Q_{i,\text{target}}(s', \tilde{a}') - \alpha \log \pi(\tilde{a}'|s')\right)$$

**Actor 損失**:
$$\mathcal{L}_\pi = \mathbb{E}_{s\sim\mathcal{D}}\left[\alpha \log \pi(\tilde{a}|s) - \min_{i=1,2} Q_i(s, \tilde{a})\right]$$

**熵溫度 $\alpha$ 損失**（可選）:
$$\mathcal{L}_\alpha = \mathbb{E}_{s\sim\mathcal{D}}\left[-\alpha \log \pi(\tilde{a}|s) - \alpha \mathcal{H}_{\text{target}}\right]$$

其中 $\mathcal{H}_{\text{target}} = -\dim(\mathcal{A})$ 為目標熵。

## 使用場景

- 連續動作空間的機器人控制任務（如行走、跑步）
- 需要穩定且高效樣本利用率的強化學習問題
- 需要兼顧探索與利用的複雜控制任務

## 優缺點

| 優點 | 缺點 |
|------|------|
| 樣本效率高（離策略學習） | 超參數較多（$\alpha$、$\tau$ 等） |
| Twin Critic 減輕 Q 值高估 | 對獎勵縮放敏感 |
| 自動熵調整減少手動調參 | 訓練計算量較大 |
| 策略隨機性促進探索 | 需要較大的回放緩衝區 |
