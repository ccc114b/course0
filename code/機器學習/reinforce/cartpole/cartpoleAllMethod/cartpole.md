# CartPole 強化學習整合訓練腳本

## 原理

此為 CartPole-v1 環境的整合訓練腳本，提供一個統一的測試框架，可載入不同的強化學習代理（Agent）進行訓練與評估。使用者只需修改一行 import/初始化程式碼即可切換演算法。

支援的代理包含：
- **VPGAgent**：Vanilla Policy Gradient (REINFORCE)
- **VPGwBaselineAgent**：帶基線的 VPG
- **DQNAgent**：Deep Q-Network
- **SARSAAgent**：SARSA
- **ActorCriticAgent**：Actor-Critic

訓練流程包含訓練階段與測試階段，並會繪製訓練過程的報酬曲線。

## 演算法步驟

1. 設定 logging，建立 CartPole-v1 環境
2. 選擇並初始化其中一個代理
3. **訓練階段**：
   - 對每個回合執行 `play_episode(env, agent, mode='train')`
   - 記錄每回合報酬
   - 若最近 20 回合平均報酬超過閾值則停止訓練
   - 繪製訓練報酬曲線
4. **測試階段**：
   - 執行 100 個測試回合
   - 計算平均報酬與標準差
5. **視覺化展示**：以 human 模式播放一次完整回合

## 數學公式

**通用訓練流程**:
$$\text{每回合: } \tau_i \sim \pi_\theta(\cdot), \quad R_i = \sum_{t} r_t$$
$$\text{停止條件: } \frac{1}{20}\sum_{i=n-19}^{n} R_i > \text{threshold}$$

## 使用場景

- 多種強化學習演算法的比較實驗
- 快速原型設計與演算法測試
- 理解不同演算法在相同環境下的表現差異

## 優缺點

| 優點 | 缺點 |
|------|------|
| 統一的訓練/測試介面 | 需要依賴各代理的特定實作 |
| 易於切換不同演算法 | 各演算法的超參數未單獨優化 |
| 包含完整的訓練流程與視覺化 | 不支援連續動作空間的環境 |
