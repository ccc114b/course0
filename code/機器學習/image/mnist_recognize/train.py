import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# 裝置自動選擇：CUDA > MPS（Apple Silicon） > CPU
device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")

class Net(nn.Module):
    """簡單 CNN 分類器：2 層卷積 + 2 層全連接
    
    輸入：28×28 灰階影像
    輸出：10 維 logits（對應 0-9 數字）
    """
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3)
        self.conv2 = nn.Conv2d(32, 64, 3)
        self.fc1 = nn.Linear(64 * 5 * 5, 128)
        self.fc2 = nn.Linear(128, 10)
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = torch.max_pool2d(x, 2)
        x = torch.relu(self.conv2(x))
        x = torch.max_pool2d(x, 2)
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)

def train():
    # 資料擴增：隨機旋轉 ±10° 以提升泛化能力
    transform = transforms.Compose([
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])

    trainSet = datasets.MNIST(root="./data", train=True, download=True, transform=transform)
    trainLoader = DataLoader(trainSet, batch_size=64, shuffle=True)

    model = Net().to(device)
    criterion = nn.CrossEntropyLoss()      # 內含 Softmax
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    model.train()
    for epoch in range(5):
        total = 0
        correct = 0
        for images, labels in trainLoader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        print(f"Epoch {epoch+1}: {100*correct/total:.2f}%")

    torch.save(model.state_dict(), "model.pth")
    print("Model saved to model.pth")

if __name__ == "__main__":
    train()