# GAN 生成器 — 手寫數字生成（mnistGanGen）

## 原理

同 `mnist_gan_gen/generate.md`。本目錄為同一 GAN 實作的不同版本拷貝，功能完全相同。

生成器使用轉置卷積將 100 維的潛在向量逐步放大為 28×28 的灰階影像。詳見 `mnist_gan_gen/generate.md`。

### 演算法步驟

1. 載入訓練好的生成器權重
2. 從標準常態取樣 z ~ N(0, I)，形狀 (N, 100)
3. 通過生成器：全連接 → Reshape → 轉置卷積 → 轉置卷積 → Tanh
4. 儲存生成的單張影像與網格組合圖

### 數學公式

同 `mnist_gan_gen/generate.md`

## 使用場景

同 `mnist_gan_gen/generate.md`

## 優缺點

同 `mnist_gan_gen/generate.md`
