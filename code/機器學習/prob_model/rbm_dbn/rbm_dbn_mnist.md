# 受限波茲曼機與深度信念網路

## 原理

本程式實作**受限波茲曼機（Restricted Boltzmann Machine, RBM）** 與**深度信念網路（Deep Belief Network, DBN）**，並應用於 MNIST 手寫數字的重建任務。

RBM 是一種生成式隨機神經網路，由可視層 $v$ 與隱藏層 $h$ 構成，層內無連線（受限）。透過**對比散度（Contrastive Divergence, CD-k）** 演算法進行近似最大概似估計訓練。

DBN 則將多層 RBM 堆疊，以**逐層貪婪預訓練（Greedy Layer-wise Pretraining）** 的方式，從底層開始逐層訓練每個 RBM，將前一層隱藏層輸出作為下一層的輸入。

### 演算法步驟

1. **資料預處理**：將 MNIST 圖像攤平為 784 維向量，並做二值化（>0.5 → 1）。
2. **RBM 訓練（CD-k）**：
   - 正相位：根據真實資料計算隱藏層機率與樣本。
   - 負相位：從隱藏層出發，進行 k 步 Gibbs 採樣得到重建。
   - 根據正負相位差異手動更新權重。
3. **DBN 逐層訓練**：
   - 第一層 RBM 直接以原始 MNIST 資料訓練。
   - 後續層以前一層 RBM 的隱藏層激活機率作為輸入。
4. **重建測試**：將測試圖片通過 DBN 正向傳播再反向重建，視覺化原始與重建結果。

### 數學公式

**RBM 能量函數**:
$$E(v, h) = -v^T W h - b^T v - c^T h$$

**條件機率（二元單元）**:
$$P(h_j = 1 \mid v) = \sigma\left(\sum_i W_{ij} v_i + c_j\right)$$
$$P(v_i = 1 \mid h) = \sigma\left(\sum_j W_{ij} h_j + b_i\right)$$

**對比散度權重更新**:
$$\Delta W = \frac{1}{N}\left( v_0^T P(h_0 \mid v_0) - v_k^T P(h_k \mid v_k) \right)$$
$$\Delta b = \frac{1}{N} \sum (v_0 - v_k)$$
$$\Delta c = \frac{1}{N} \sum (P(h_0 \mid v_0) - P(h_k \mid v_k))$$

**重建誤差（均方誤差）**:
$$\text{Recon Error} = \frac{1}{N} \sum_i (v_{0,i} - v_{k,i})^2$$

## 使用場景

- 無監督特徵提取與表示學習
- 深度生成模型的教學入門
- 資料降維與重建任務

## 優缺點

| 優點 | 缺點 |
|------|------|
| 無監督學習，不需要標籤 | CD-k 近似梯度有偏 |
| 逐層預訓練可緩解深層網路訓練困難 | 二值化處理可能損失資訊 |
| 結構簡單，易於理解生成式模型 | 訓練收斂速度較慢 |
| 可視化重建效果直觀 | 無 softmax 可見層，不適合多值資料 |
