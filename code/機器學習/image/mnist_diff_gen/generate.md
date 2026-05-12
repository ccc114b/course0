# DDPM 與 DDIM 採樣演算法

## 原理

擴散模型（Diffusion Model）的核心思想是：先定義一個前向過程，逐步將真實資料 x₀ 加噪成純高斯噪聲 x_T；然後訓練一個神經網路來**逆向**這個過程，從純噪聲逐步還原出清晰資料。生成階段就是執行這個逆向過程。

DDPM（Denoising Diffusion Probabilistic Models）採用完整的 T 步馬可夫鏈逆向採樣；DDIM（Denoising Diffusion Implicit Models）則是 DDPM 的加速變體，透過將逆向過程改為非馬可夫式，允許跳步採樣來大幅減少步數。

### 演算法步驟（DDPM 逆向採樣）

1. 從標準常態分佈取樣 x_T ~ N(0, I)
2. 對 t = T, T-1, ..., 1 迭代：
   a. 用 UNet 預測當前噪聲 ε_θ(x_t, t)
   b. 估計原始資料：x̂₀ = (x_t - √(1-ᾱ_t) · ε_θ) / √(ᾱ_t)
   c. 計算後驗均值：μ̃(x_t, x̂₀) = (√(ᾱ_{t-1})·β_t/(1-ᾱ_t)) · x̂₀ + (√(α_t)·(1-ᾱ_{t-1})/(1-ᾱ_t)) · x_t
   d. 若 t > 0，加入後驗變異數的噪聲：x_{t-1} = μ̃ + σ_t · z, z ~ N(0, I)
3. 回傳 x₀

### 演算法步驟（DDIM 快速採樣）

1. 從標準常態分佈取樣 x_T
2. 選取子步驟序列 τ = [τ₁, τ₂, ..., τ_S]（S << T）
3. 對每個子步驟迭代：
   a. 用 UNet 預測噪聲 ε_θ(x_{τ_i}, τ_i)
   b. 估計 x̂₀
   c. DDIM 更新：x_{τ_{i-1}} = √(ᾱ_{τ_{i-1}}) · x̂₀ + √(1-ᾱ_{τ_{i-1}} - σ²) · ε_θ + σ · z
   d. 其中 η（eta）控制 σ 的大小：η=0 為完全確定性，η=1 等同 DDPM

### 數學公式

**前向擴散過程**:
$$q(x_t | x_0) = \mathcal{N}(x_t; \sqrt{\bar{\alpha}_t} x_0, (1-\bar{\alpha}_t)I)$$

**逆向去噪均值**:
$$\tilde{\mu}(x_t, x_0) = \frac{\sqrt{\bar{\alpha}_{t-1}}\beta_t}{1-\bar{\alpha}_t} x_0 + \frac{\sqrt{\alpha_t}(1-\bar{\alpha}_{t-1})}{1-\bar{\alpha}_t} x_t$$

**DDIM 更新式**:
$$x_{\tau_{i-1}} = \sqrt{\bar{\alpha}_{\tau_{i-1}}} \hat{x}_0 + \sqrt{1-\bar{\alpha}_{\tau_{i-1}} - \sigma^2} \cdot \epsilon_\theta + \sigma \cdot z$$

## 使用場景

- 影像生成（本程式為 MNIST 手寫數字生成）
- 影像修復、超解析度、填補
- 文字轉影像（如 DALL·E、Stable Diffusion）
- 任何需要高品質生成式模型的任務

## 優缺點

| 優點 | 缺點 |
|------|------|
| 生成品質高，超越 GAN | 取樣速度慢（DDPM 需千步） |
| 訓練穩定，無對抗訓練 | DDIM 在極少步數下品質下降 |
| 數學框架清晰，易於擴展 | 模型參數量大 |
| DDIM 可在品質與速度間取捨 | 仍比 GAN 耗時 |
