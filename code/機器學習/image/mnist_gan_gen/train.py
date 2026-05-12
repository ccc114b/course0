import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import os

# 自動選擇計算裝置：CUDA > MPS > CPU
if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

latent_dim = 100   # 生成器的潛在空間維度
img_size = 28      # MNIST 圖片尺寸
channels = 1       # 灰階

class Generator(nn.Module):
    """生成器：從隨機噪聲生成手寫數字
    
    結構：全連接層 → Reshape → 轉置卷積(上採樣) → 轉置卷積 → Tanh
    輸入：z ∈ R^100（標準常態分佈）
    輸出：28×28 灰階影像，值域 [-1, 1]
    """
    def __init__(self):
        super().__init__()
        self.l0 = nn.Linear(latent_dim, 7 * 7 * 64)
        self.conv1 = nn.ConvTranspose2d(64, 32, 4, 2, 1)
        self.conv2 = nn.ConvTranspose2d(32, 1, 4, 2, 1)
        self.bn1 = nn.BatchNorm2d(32)
        self.act = nn.ReLU(True)
        self.out = nn.Tanh()

    def forward(self, z):
        out = self.l0(z).view(-1, 64, 7, 7)
        out = self.act(self.bn1(self.conv1(out)))
        out = self.out(self.conv2(out))
        return out

class Discriminator(nn.Module):
    """判別器：區分真實 MNIST 圖片與偽造圖片
    
    結構：卷積(下採樣) → Dropout → 卷積(下採樣) → 全連接 → 輸出
    輸出為單一 logit（未經 sigmoid），配合 BCEWithLogitsLoss 使用
    """
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 4, 2, 1)
        self.conv2 = nn.Conv2d(32, 64, 4, 2, 1)
        self.fc = nn.Linear(64 * 7 * 7, 1)
        self.act = nn.LeakyReLU(0.2, True)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        out = self.act(self.conv1(x))
        out = self.dropout(out)
        out = self.act(self.conv2(out))
        out = out.view(out.size(0), -1)
        out = self.fc(out)
        return out

def train(epochs=30, batch_size=256, lr=0.001):
    # 資料預處理：歸一化至 [-1, 1] 以匹配生成器 Tanh 輸出
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])

    dataset = datasets.MNIST(root="./data", train=True, download=True, transform=transform)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=2)

    generator = Generator().to(device)
    discriminator = Discriminator().to(device)

    # 對抗損失：二分類的 BCE，輸出層無 sigmoid
    adversarial_loss = nn.BCEWithLogitsLoss()
    optimizer_g = optim.Adam(generator.parameters(), lr=lr, betas=(0.5, 0.999))
    optimizer_d = optim.Adam(discriminator.parameters(), lr=lr, betas=(0.5, 0.999))

    os.makedirs("weights", exist_ok=True)

    for epoch in range(epochs):
        epoch_loss_g = 0
        epoch_loss_d = 0
        for i, (imgs, _) in enumerate(dataloader):
            batch = imgs.size(0)
            real = torch.ones(batch, 1).to(device)   # 真實標籤：1
            fake = torch.zeros(batch, 1).to(device)  # 偽造標籤：0

            # ─── 訓練判別器 ───
            # 目標：對真實圖片輸出 1，對偽造圖片輸出 0
            imgs = imgs.to(device)
            optimizer_d.zero_grad()
            real_validity = discriminator(imgs)
            real_loss = adversarial_loss(real_validity, real)

            z = torch.randn(batch, latent_dim).to(device)
            fake_imgs = generator(z).detach()
            fake_validity = discriminator(fake_imgs)
            fake_loss = adversarial_loss(fake_validity, fake)

            d_loss = (real_loss + fake_loss) / 2
            d_loss.backward()
            optimizer_d.step()
            epoch_loss_d += d_loss.item()

            # ─── 訓練生成器 ───
            # 目標：讓判別器對偽造圖片輸出 1（欺騙判別器）
            optimizer_g.zero_grad()
            z = torch.randn(batch, latent_dim).to(device)
            gen_imgs = generator(z)
            validity = discriminator(gen_imgs)
            g_loss = adversarial_loss(validity, real)
            g_loss.backward()
            optimizer_g.step()
            epoch_loss_g += g_loss.item()

        avg_g_loss = epoch_loss_g / len(dataloader)
        avg_d_loss = epoch_loss_d / len(dataloader)
        print(f"Epoch {epoch+1}/{epochs} - D_loss: {avg_d_loss:.4f}, G_loss: {avg_g_loss:.4f}")

        # 每 10 個 epoch 儲存一次權重
        if (epoch + 1) % 10 == 0:
            torch.save({
                "generator": generator.state_dict(),
                "discriminator": discriminator.state_dict(),
            }, f"weights/gan_{epoch+1}.pth")
            print(f"Saved weights/gan_{epoch+1}.pth")

    # 儲存最終模型
    torch.save({
        "generator": generator.state_dict(),
        "discriminator": discriminator.state_dict(),
    }, "weights/gan_final.pth")
    print("Training complete. Saved to weights/gan_final.pth")

if __name__ == "__main__":
    train()