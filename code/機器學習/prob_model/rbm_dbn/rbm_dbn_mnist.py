import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from torchvision import datasets, transforms

# ---------- 1. 運算裝置選擇（支援 MPS / CUDA / CPU） ----------
if torch.backends.mps.is_available():
    device = torch.device("mps")
elif torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")
print(f"使用裝置：{device}")


# ---------- 2. 載入 MNIST 資料集 ----------
# 將影像攤平成 784 維向量，並做二值化（像素 > 0.5 設為 1，其餘為 0）
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Lambda(lambda x: (x.view(-1) > 0.5).float())  # 攤平 + 二值化
])

train_dataset = datasets.MNIST(root='./data', train=True,  download=True, transform=transform)
test_dataset  = datasets.MNIST(root='./data', train=False, download=True, transform=transform)

train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=128, shuffle=True)
test_loader  = torch.utils.data.DataLoader(test_dataset,  batch_size=200, shuffle=False)


# ---------- 3. RBM（受限波茲曼機）實作 ----------
class RBM(nn.Module):
    """
    受限波茲曼機（Restricted Boltzmann Machine, RBM）。
    由可視層 v 與隱藏層 h 組成，層內無連線。
    訓練使用對比散度演算法（Contrastive Divergence, CD-k）。
    """
    def __init__(self, n_visible, n_hidden, lr=0.01, k=1):
        super().__init__()
        self.n_visible = n_visible
        self.n_hidden  = n_hidden
        self.lr        = lr
        self.k         = k          # Gibbs 採樣步數
        self.errors    = []         # 記錄每個 epoch 的平均重建誤差

        # 使用 Xavier/Glorot 初始化的變體來初始化權重矩陣
        scale = (2.0 / (n_visible + n_hidden)) ** 0.5
        self.W = nn.Parameter(torch.randn(n_visible, n_hidden) * scale)  # 可視層↔隱藏層權重
        self.b = nn.Parameter(torch.zeros(n_visible))                     # 可視層偏置
        self.c = nn.Parameter(torch.zeros(n_hidden))                      # 隱藏層偏置

    def sample_h(self, v):
        """
        給定可視層 v，計算隱藏層的激活機率並進行伯努利採樣。
        回傳 (機率, 採樣結果)。
        """
        prob   = torch.sigmoid(v @ self.W + self.c)
        sample = torch.bernoulli(prob)
        return prob, sample

    def sample_v(self, h):
        """
        給定隱藏層 h，計算可視層的激活機率並進行伯努利採樣。
        回傳 (機率, 採樣結果)。
        """
        prob   = torch.sigmoid(h @ self.W.t() + self.b)
        sample = torch.bernoulli(prob)
        return prob, sample

    @torch.no_grad()
    def contrastive_divergence(self, v0):
        """
        執行 CD-k 演算法對權重進行更新：
        1. 正相位：根據真實資料計算隱藏層機率 ph0。
        2. k 步 Gibbs 採樣：從 ph0 → vk → hk 交替採樣。
        3. 根據正負相位的差異手動更新權重。
        
        回傳重建誤差（MSE）。
        """
        # 正相位：真實資料對應的隱藏層激活
        ph0, h0 = self.sample_h(v0)

        # k 步 Gibbs 採樣，產生「負相位」樣本
        vk, hk, phk = v0.clone(), h0.clone(), ph0.clone()
        for _ in range(self.k):
            _, vk   = self.sample_v(hk)
            phk, hk = self.sample_h(vk)

        # 手動計算梯度並更新（CD-k 不走 autograd，直接操作 data 屬性）
        batch = v0.shape[0]
        dW = (v0.t() @ ph0 - vk.t() @ phk) / batch
        db = (v0 - vk).mean(dim=0)
        dc = (ph0 - phk).mean(dim=0)

        self.W.data += self.lr * dW
        self.b.data += self.lr * db
        self.c.data += self.lr * dc

        # 計算當前 batch 的重建誤差（MSE）
        recon_err = torch.mean((v0 - vk) ** 2).item()
        return recon_err

    def fit(self, loader, epochs=10, verbose=True):
        """在多個 epoch 上訓練 RBM。"""
        self.to(device)
        for epoch in range(1, epochs + 1):
            errs = []
            for x, _ in loader:
                x = x.to(device)
                err = self.contrastive_divergence(x)
                errs.append(err)
            mean_err = np.mean(errs)
            self.errors.append(mean_err)
            if verbose:
                print(f"  Epoch {epoch:3d}/{epochs}  Recon Error: {mean_err:.5f}")

    @torch.no_grad()
    def transform(self, x):
        """將輸入資料轉換為隱藏層的激活機率（用於提取特徵）。"""
        prob, _ = self.sample_h(x.to(device))
        return prob

    @torch.no_grad()
    def reconstruct(self, x):
        """對輸入進行正向傳播（v→h）再反向重建（h→v），回傳重建的可視層機率。"""
        _, h = self.sample_h(x.to(device))
        prob_v, _ = self.sample_v(h)
        return prob_v


# ---------- 4. DBN（深度信念網路）實作 ----------
class DBN:
    """
    深度信念網路（Deep Belief Network, DBN）。
    將多層 RBM 逐層堆疊，以貪婪無監督方式逐層預訓練。
    """
    def __init__(self, layer_sizes, lr=0.01, k=1):
        # 根據指定的每層神經元數量建立對應的 RBM 列表
        self.rbms = [
            RBM(layer_sizes[i], layer_sizes[i+1], lr=lr, k=k)
            for i in range(len(layer_sizes) - 1)
        ]

    def fit(self, loader, epochs=10):
        """
        逐層訓練 DBN：
        - 第一層 RBM 直接使用原始資料訓練
        - 後續層 RBM 使用前一層 RBM 的隱藏層激活機率作為輸入
        """
        current_data = None

        for i, rbm in enumerate(self.rbms):
            print(f"\n{'='*50}")
            print(f" 訓練第 {i+1} 層 RBM  ({rbm.n_visible} → {rbm.n_hidden})")
            print('='*50)

            if i == 0:
                # 第一層：直接使用原始 MNIST 資料
                rbm.fit(loader, epochs=epochs)
                # 收集全部資料通過第一層後的隱藏層激活值，作為下一層的輸入
                feats = []
                for x, _ in loader:
                    feats.append(rbm.transform(x).cpu())
                current_data = torch.cat(feats, dim=0)
            else:
                # 後續層：使用前一層的輸出作為訓練資料
                ds  = torch.utils.data.TensorDataset(current_data,
                            torch.zeros(current_data.shape[0]))
                ldr = torch.utils.data.DataLoader(ds, batch_size=128, shuffle=True)
                rbm.fit(ldr, epochs=epochs)
                # 收集下一層的輸入
                feats = []
                for x, _ in ldr:
                    feats.append(rbm.transform(x).cpu())
                current_data = torch.cat(feats, dim=0)

    @torch.no_grad()
    def reconstruct(self, x):
        """
        重建流程：
        1. 正向傳播：將輸入逐層傳遞至最上層
        2. 反向傳播：從最上層逐層重建回可視層
        回傳重建機率（在 CPU 上）。
        """
        # 逐層正向：v → h1 → h2 → ...
        data = x.to(device)
        for rbm in self.rbms:
            _, data = rbm.sample_h(data)

        # 逐層反向重建：... → h2 → h1 → v
        for rbm in reversed(self.rbms):
            prob, data = rbm.sample_v(data)
        return prob.cpu()


# ---------- 5. 建立並訓練 DBN：784 → 256 → 64 ----------
dbn = DBN(layer_sizes=[784, 256, 64], lr=0.01, k=1)
dbn.fit(train_loader, epochs=15)


# ---------- 6. 視覺化：重建效果 ----------
# 從測試集中取一批資料，顯示原始圖像與 DBN 重建結果的對比
test_x, _ = next(iter(test_loader))
samples = test_x[:10]
recon   = dbn.reconstruct(samples)

fig, axes = plt.subplots(2, 10, figsize=(15, 3))
for i in range(10):
    # 第一列：原始影像
    axes[0, i].imshow(samples[i].view(28, 28).numpy(), cmap="gray")
    axes[0, i].axis("off")
    # 第二列：DBN 重建的影像
    axes[1, i].imshow(recon[i].view(28, 28).numpy(), cmap="gray")
    axes[1, i].axis("off")

axes[0, 0].set_ylabel("原始", fontsize=11)
axes[1, 0].set_ylabel("重建", fontsize=11)
plt.suptitle("DBN 重建效果（784→256→64）", fontsize=13)
plt.tight_layout()
plt.savefig("dbn_reconstruction.png", dpi=120)
plt.show()


# ---------- 7. 視覺化：各層訓練誤差曲線 ----------
fig, axes = plt.subplots(1, len(dbn.rbms), figsize=(12, 4))
for i, rbm in enumerate(dbn.rbms):
    axes[i].plot(rbm.errors, marker='o', markersize=3)
    axes[i].set_title(f"RBM {i+1}（{rbm.n_visible}→{rbm.n_hidden}）")
    axes[i].set_xlabel("Epoch")
    axes[i].set_ylabel("重建誤差 (MSE)")
    axes[i].grid(True, alpha=0.3)

plt.suptitle("各層 RBM 訓練誤差曲線", fontsize=13)
plt.tight_layout()
plt.savefig("dbn_training_curves.png", dpi=120)
plt.show()

print("\n完成！圖片已儲存。")
