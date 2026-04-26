import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from torchvision import datasets, transforms

# ─────────────────────────────────────────
# 1. 裝置選擇（支援 MPS / CUDA / CPU）
# ─────────────────────────────────────────
if torch.backends.mps.is_available():
    device = torch.device("mps")
elif torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")
print(f"使用裝置：{device}")


# ─────────────────────────────────────────
# 2. 載入 MNIST
# ─────────────────────────────────────────
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Lambda(lambda x: (x.view(-1) > 0.5).float())  # 攤平784 + 二值化
])

train_dataset = datasets.MNIST(root='./data', train=True,  download=True, transform=transform)
test_dataset  = datasets.MNIST(root='./data', train=False, download=True, transform=transform)

train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=128, shuffle=True)
test_loader  = torch.utils.data.DataLoader(test_dataset,  batch_size=200, shuffle=False)


# ─────────────────────────────────────────
# 3. RBM 類別（CD-k）
# ─────────────────────────────────────────
class RBM(nn.Module):
    def __init__(self, n_visible, n_hidden, lr=0.01, k=1):
        super().__init__()
        self.n_visible = n_visible
        self.n_hidden  = n_hidden
        self.lr        = lr
        self.k         = k
        self.errors    = []

        scale = (2.0 / (n_visible + n_hidden)) ** 0.5
        self.W = nn.Parameter(torch.randn(n_visible, n_hidden) * scale)
        self.b = nn.Parameter(torch.zeros(n_visible))
        self.c = nn.Parameter(torch.zeros(n_hidden))

    def sample_h(self, v):
        prob   = torch.sigmoid(v @ self.W + self.c)
        sample = torch.bernoulli(prob)
        return prob, sample

    def sample_v(self, h):
        prob   = torch.sigmoid(h @ self.W.t() + self.b)
        sample = torch.bernoulli(prob)
        return prob, sample

    @torch.no_grad()
    def contrastive_divergence(self, v0):
        # 正相位
        ph0, h0 = self.sample_h(v0)

        # k 步 Gibbs 採樣（負相位）
        vk, hk, phk = v0.clone(), h0.clone(), ph0.clone()
        for _ in range(self.k):
            _, vk   = self.sample_v(hk)
            phk, hk = self.sample_h(vk)

        # 手動梯度更新（CD 不走 autograd）
        batch = v0.shape[0]
        dW = (v0.t() @ ph0 - vk.t() @ phk) / batch
        db = (v0 - vk).mean(dim=0)
        dc = (ph0 - phk).mean(dim=0)

        self.W.data += self.lr * dW
        self.b.data += self.lr * db
        self.c.data += self.lr * dc

        recon_err = torch.mean((v0 - vk) ** 2).item()
        return recon_err

    def fit(self, loader, epochs=10, verbose=True):
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
        prob, _ = self.sample_h(x.to(device))
        return prob

    @torch.no_grad()
    def reconstruct(self, x):
        _, h = self.sample_h(x.to(device))
        prob_v, _ = self.sample_v(h)
        return prob_v


# ─────────────────────────────────────────
# 4. DBN 類別（逐層貪婪預訓練）
# ─────────────────────────────────────────
class DBN:
    def __init__(self, layer_sizes, lr=0.01, k=1):
        self.rbms = [
            RBM(layer_sizes[i], layer_sizes[i+1], lr=lr, k=k)
            for i in range(len(layer_sizes) - 1)
        ]

    def fit(self, loader, epochs=10):
        # 第一層直接用原始 DataLoader
        current_data = None

        for i, rbm in enumerate(self.rbms):
            print(f"\n{'='*50}")
            print(f" 訓練第 {i+1} 層 RBM  ({rbm.n_visible} → {rbm.n_hidden})")
            print('='*50)

            if i == 0:
                rbm.fit(loader, epochs=epochs)
                # 收集第一層輸出作為第二層輸入
                feats = []
                for x, _ in loader:
                    feats.append(rbm.transform(x).cpu())
                current_data = torch.cat(feats, dim=0)
            else:
                # 包成 TensorDataset + DataLoader
                ds     = torch.utils.data.TensorDataset(current_data,
                            torch.zeros(current_data.shape[0]))
                ldr    = torch.utils.data.DataLoader(ds, batch_size=128, shuffle=True)
                rbm.fit(ldr, epochs=epochs)
                # 收集輸出
                feats = []
                for x, _ in ldr:
                    feats.append(rbm.transform(x).cpu())
                current_data = torch.cat(feats, dim=0)

    @torch.no_grad()
    def reconstruct(self, x):
        # 正向：逐層取隱藏層樣本
        data = x.to(device)
        for rbm in self.rbms:
            _, data = rbm.sample_h(data)

        # 反向：逐層重建
        for rbm in reversed(self.rbms):
            prob, data = rbm.sample_v(data)
        return prob.cpu()


# ─────────────────────────────────────────
# 5. 建立並訓練 DBN：784 → 256 → 64
# ─────────────────────────────────────────
dbn = DBN(layer_sizes=[784, 256, 64], lr=0.01, k=1)
dbn.fit(train_loader, epochs=15)


# ─────────────────────────────────────────
# 6. 視覺化：重建效果
# ─────────────────────────────────────────
test_x, _ = next(iter(test_loader))   # 取一批測試圖
samples = test_x[:10]                 # 取前 10 張
recon   = dbn.reconstruct(samples)

fig, axes = plt.subplots(2, 10, figsize=(15, 3))
for i in range(10):
    axes[0, i].imshow(samples[i].view(28, 28).numpy(), cmap="gray")
    axes[0, i].axis("off")
    axes[1, i].imshow(recon[i].view(28, 28).numpy(), cmap="gray")
    axes[1, i].axis("off")

axes[0, 0].set_ylabel("原始", fontsize=11)
axes[1, 0].set_ylabel("重建", fontsize=11)
plt.suptitle("DBN 重建效果（784→256→64）", fontsize=13)
plt.tight_layout()
plt.savefig("dbn_reconstruction.png", dpi=120)
plt.show()


# ─────────────────────────────────────────
# 7. 視覺化：各層訓練誤差曲線
# ─────────────────────────────────────────
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