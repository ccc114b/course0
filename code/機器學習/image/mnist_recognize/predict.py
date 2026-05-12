import torch
import torchvision.transforms as transforms
from torch import nn
from PIL import Image

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 圖片預處理流水線：灰階化 → 縮放至 28×28 → 正規化至 [-1, 1]
transform = transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize((28, 28)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

class Net(nn.Module):
    """簡單 CNN 分類器：2 層卷積 + 2 層全連接
    
    卷積層使用 3×3 卷積核，配合 2×2 MaxPool 下採樣。
    最後一層全連接輸出 10 個 logits 對應 0-9 數字。
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

def predict(image_path):
    # 載入模型權重，設為評估模式（關閉 Dropout）
    model = Net().to(device)
    model.load_state_dict(torch.load("model.pth", map_location=device))
    model.eval()

    image = Image.open(image_path)
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(image)
        pred = torch.max(output, 1)[1].item()

    print(f"Predicted: {pred}")
    return pred

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        predict(sys.argv[1])
    else:
        print("Usage: python predict.py <image_path>")