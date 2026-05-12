# DDPM 訓練演算法（Denoising Diffusion Probabilistic Model）

## 原理

DDPM 的訓練目標是讓神經網路學會**預測加入的噪聲**。給定一張乾淨圖片 x₀，我們隨機選取一個時間步 t，根據前向公式直接計算出 x_t，然後讓模型預測所加的噪聲 ε。損失函數是預測噪聲與真實噪聲之間的均方誤差（MSE）。

這個目標等價於最大化變分下界（ELBO），能夠保證模型學到真實的資料分佈。

### 演算法步驟

1. 從資料集取樣 x₀
2. 隨機選取時間步 t ~ Uniform({1, ..., T})
3. 從標準常態取樣噪聲 ε ~ N(0, I)
4. 計算加噪後的 x_t = √(ᾱ_t) · x₀ + √(1-ᾱ_t) · ε
5. 用 UNet 預測噪聲 ε̂ = ε_θ(x_t, t)
6. 計算損失 L = ||ε - ε̂||²
7. 反向傳播更新 UNet 參數
8. 重複直到收斂

### 數學公式

**加噪公式**:
$$x_t = \sqrt{\bar{\alpha}_t} x_0 + \sqrt{1-\bar{\alpha}_t} \epsilon, \quad \epsilon \sim \mathcal{N}(0, I)$$

**訓練損失**:
$$L_{\text{simple}} = \mathbb{E}_{x_0, t, \epsilon} \left[ \|\epsilon - \epsilon_\theta(x_t, t)\|^2 \right]$$

**噪聲排程（線性排程）**:
$$\beta_t = \beta_{\text{start}} + \frac{t}{T}(\beta_{\text{end}} - \beta_{\text{start}})$$
$$\alpha_t = 1 - \beta_t$$
$$\bar{\alpha}_t = \prod_{s=1}^{t} \alpha_s$$

## 使用場景

- 生成式模型的訓練階段
- 需要學習複雜高維度資料分佈的任務
- 後續可用於影像生成、填補、編輯等

## 優缺點

| 優點 | 缺點 |
|------|------|
| 訓練穩定，無模式崩潰 | 生成速度慢（需逐步迭代） |
| 損失函數簡單（MSE） | 需要較多超參數調校（T, β 排程） |
| 可擴展至條件生成 | 訓練計算量大 |
| 數學理論完備 | 需要大量取樣步數 |
