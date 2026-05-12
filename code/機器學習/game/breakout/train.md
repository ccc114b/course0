# Breakout DQN 訓練器

## 原理

本程式實作 **Deep Q-Network (DQN)** 演算法訓練 Atari Breakout 遊戲。DQN 由 Mnih et al. (2015) 提出，結合以下關鍵技術：

1. **經驗回放（Experience Replay）**：將轉移 `(s, a, r, s', done)` 儲存於回放緩衝區，每次從中隨機抽樣 mini-batch 訓練，打破時間相關性。
2. **目標網路（Target Network）**：使用一個凍結的目標網路計算 TD target，定期與策略網路同步，穩定訓練。
3. **卷積神經網路**：將原始畫素作為輸入，自動學習空間特徵。

獎勵被裁切至 `[-1, 1]` 範圍，並使用 Huber Loss（`smooth_l1_loss`）進行訓練。

### 演算法步驟

1. **初始化**：建立策略網路 $Q_\theta$、目標網路 $Q_{\theta^-}$、經驗回放池 $D$。
2. **收集經驗**：以 ε-greedy 策略執行動作，將 `(s, a, r, s', done)` 存入 $D$。
3. **訓練**：從 $D$ 採樣 batch，計算 TD target 與損失，更新 $\theta$。
4. **同步目標網路**：每 $N$ 步將 $\theta^- \leftarrow \theta$。
5. **探索率衰減**：ε 從 1.0 線性衰減至 0.05。
6. **檢查點**：定期儲存模型權重與訓練狀態，並保留最佳模型。

### 數學公式

**TD Target**:
$$y = r + \gamma \cdot \max_{a'} Q_{\theta^-}(s', a') \cdot (1 - \text{done})$$

**Huber Loss**:
$$\mathcal{L}(\theta) = \begin{cases}
\frac{1}{2}(y - Q_\theta(s,a))^2 & \text{if } |y - Q_\theta(s,a)| \leq 1 \\
|y - Q_\theta(s,a)| - \frac{1}{2} & \text{otherwise}
\end{cases}$$

**ε-greedy 探索率衰減**:
$$\varepsilon(t) = \varepsilon_{\text{start}} + (\varepsilon_{\text{end}} - \varepsilon_{\text{start}}) \cdot \min\left(\frac{t}{T_{\text{decay}}}, 1\right)$$

## 使用場景

- 深度強化學習經典演算法教學
- Atari 遊戲的 AI 訓練
- 作為 DQN 系列架構的基線實作

## 優缺點

| 優點 | 缺點 |
|------|------|
| 經典可靠的實作方式 | 訓練耗時（需數千回合） |
| 支援從 checkpoint 繼續訓練 | 記憶體佔用隨 replay buffer 增大 |
| 自動保留最佳模型 | ε-greedy 在大狀態空間效率低 |
| 支援 CUDA / MPS 加速 | 無 Double DQN / Dueling DQN 等改良 |
