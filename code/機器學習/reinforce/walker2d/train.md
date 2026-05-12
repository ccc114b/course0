# PPO (Proximal Policy Optimization) — Walker2d-v5

## 原理

PPO 是 Trust Region Policy Optimization 的簡化版本，透過裁剪（Clipping）機制限制每次更新的幅度，避免策略在單次更新中變化過大導致崩潰。核心思想是在每次更新時，新舊策略的比率被限制在 $[1 - \epsilon, 1 + \epsilon]$ 範圍內。

此實作使用以下 PPO 組件：
- **Actor-Critic 架構**：共享特徵提取層但輸出不同頭部
- **GAE 風格的優勢計算**：使用簡化的優勢估計（Returns - Values）
- **狀態歸一化**：使用 RunningMeanStd 線上更新
- **獎勵縮放**：將原始獎勵除以 10 以穩定訓練
- **多輪更新**：每次收集數據後進行 10 輪 PPO 更新

## 演算法步驟

1. 初始化 Actor-Critic 網路、優化器、狀態歸一化器
2. 對每次更新迭代（共 1000 次）：
   a. **收集數據**：使用當前策略執行 2048 步，記錄狀態、動作、對數機率、獎勵、終止信號
   b. **計算 Returns**：從後往前計算折扣回報
   c. **計算優勢**：$\text{Advantage} = \text{Returns} - V(s)$，並正規化
   d. **PPO 更新**（10 輪）：
      - 計算新舊策略比率 $r_t(\theta) = \frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{\text{old}}}(a_t|s_t)}$
      - 裁剪比率至 $[0.8, 1.2]$
      - 最小化組合損失（策略損失 + 價值損失 + 熵獎勵）
3. 定期保存模型與歸一化參數

## 數學公式

**PPO 裁剪目標**:
$$\mathcal{L}^{\text{CLIP}}(\theta) = \mathbb{E}_t\left[\min(r_t(\theta) A_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) A_t)\right]$$

**比率**:
$$r_t(\theta) = \frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{\text{old}}}(a_t|s_t)}$$

**總損失**:
$$\mathcal{L} = -\mathcal{L}^{\text{CLIP}} + c_1 \cdot \text{MSE}(V(s), R) - c_2 \cdot \mathcal{H}(\pi)$$

## 使用場景

- 連續動作空間的機器人控制（MuJoCo 環境）
- 需要穩定且高效訓練的強化學習任務
- 高維度狀態空間的複雜控制問題

## 優缺點

| 優點 | 缺點 |
|------|------|
| 訓練穩定，不易崩潰 | 實現比 VPG 複雜 |
| 樣本效率比基於策略的方法高 | 超參數較多（裁剪範圍、更新輪數） |
| 可適用於連續與離散動作空間 | 獎勵縮放需要手動調整 |
| 裁剪機制簡化 TRPO 的複雜計算 | 多輪更新增加計算成本 |
