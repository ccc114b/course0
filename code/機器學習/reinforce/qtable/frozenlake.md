# Q-Table 強化學習 — FrozenLake-v1

## 原理

此實作使用傳統的表格型強化學習演算法來解決 FrozenLake 問題，包含三種方法的比較：

1. **Q-Learning**（離策略）：使用 $s'$ 狀態下所有動作中的最大 Q 值來更新 $Q(s,a)$，不依賴於實際選擇的 $a'$。
2. **SARSA**（基於策略）：使用實際選擇的 $a'$ 對應的 $Q(s',a')$ 來更新 $Q(s,a)$。
3. **TD($\lambda$)**：引入資格跡（Eligibility Trace），結合 TD 誤差與資格跡矩陣，在時間與狀態空間中進行更平滑的信用分配。

FrozenLake 是一個柵格世界，智能體需要從起點走到終點，冰面光滑會導致移動方向不確定，掉入冰洞則會終止回合。

## 演算法步驟

1. 初始化 Q 表為零矩陣（大小為 16 狀態 × 4 動作）
2. 對每個回合：
   - 重置環境，取得初始狀態
   - 對每個時間步（最多 99 步）：
     a. 使用 $\epsilon$-greedy 策略選擇動作（$\epsilon$ 隨回合數遞減）
     b. 執行動作，觀察 $(s', r, \text{done})$
     c. 根據所選方法更新 Q 表：
        - **Q-Learning**: $Q(s,a) \leftarrow Q(s,a) + \alpha(r + \gamma \max_{a'} Q(s',a') - Q(s,a))$
        - **SARSA**: $Q(s,a) \leftarrow Q(s,a) + \alpha(r + \gamma Q(s',a') - Q(s,a))$
        - **TD($\lambda$)**: 更新資格跡 E，$Q \leftarrow Q + \alpha \delta E$
3. 學習完成後使用貪婪策略展示結果

## 數學公式

**Q-Learning 更新**:
$$Q(s,a) \leftarrow Q(s,a) + \alpha \left(r + \gamma \max_{a'} Q(s',a') - Q(s,a)\right)$$

**SARSA 更新**:
$$Q(s,a) \leftarrow Q(s,a) + \alpha \left(r + \gamma Q(s',a') - Q(s,a)\right)$$

**TD($\lambda$) 更新**:
$$\delta_t = r_t + \gamma Q(s_{t+1}, a_{t+1}) - Q(s_t, a_t)$$
$$E_t(s,a) = \gamma \lambda E_{t-1}(s,a) + \mathbb{1}_{\{s=s_t, a=a_t\}}$$
$$Q(s,a) \leftarrow Q(s,a) + \alpha \delta_t E_t(s,a)$$

## 使用場景

- 表格型強化學習的教學入門
- 比較離策略（Q-Learning）與基於策略（SARSA）的差異
- 理解資格跡（TD($\lambda$)）對學習效果的影響

## 優缺點

| 優點 | 缺點 |
|------|------|
| Q-Table 可解釋性強 | 狀態空間大時無法擴展 |
| 三種方法直接比較 | FrozenLake 的環境隨機性使學習困難 |
| 訓練速度快 | $\epsilon$ 衰減策略較粗糙 |
| 無需深度學習框架 | 離散狀態/動作空間限制 |
