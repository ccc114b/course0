# GAN 訓練 — 手寫數字生成（mnistGanGen）

## 原理

同 `mnist_gan_gen/train.md`。本目錄為同一 GAN 實作的不同版本拷貝。

採用生成對抗網路的 min-max 遊戲架構，生成器與判別器交替訓練。詳見 `mnist_gan_gen/train.md`。

### 演算法步驟

1. 載入 MNIST 資料集，歸一化至 [-1, 1]
2. 判別器訓練：最大化對真實圖片與偽造圖片的分類正確率
3. 生成器訓練：最小化判別器對偽造圖片的辨識能力
4. 交替更新，每 10 個 epoch 儲存權重

### 數學公式

同 `mnist_gan_gen/train.md`

## 使用場景

同 `mnist_gan_gen/train.md`

## 優缺點

同 `mnist_gan_gen/train.md`
