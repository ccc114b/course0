import torch
from torchvision import datasets, transforms
from PIL import Image

# 從 MNIST 測試集中提取前 10 張影像（每個數字各一張）作為測試圖片
transform = transforms.ToTensor()
testSet = datasets.MNIST(root="./data", train=False, download=True, transform=transform)

for i in range(10):
    img, label = testSet[i]
    img = img.squeeze().numpy()
    Image.fromarray((img * 255).astype("uint8")).save(f"img/{label}_{i}.png")
    print(f"Saved img/{label}_{i}.png (label={label})")