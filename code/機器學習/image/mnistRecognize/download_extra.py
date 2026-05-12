import torch
from torchvision import datasets, transforms
from PIL import Image

# 從 MNIST 測試集提取數字 3、6、8 各 2 張作為測試樣本
transform = transforms.ToTensor()
testSet = datasets.MNIST(root="./data", train=False, download=True, transform=transform)

needed = {3: 0, 6: 0, 8: 0}
for img, label in testSet:
    if label in needed and needed[label] < 2:
        img_np = img.squeeze().numpy()
        Image.fromarray((img_np * 255).astype("uint8")).save(f"img/{label}_{needed[label]}.png")
        print(f"Saved img/{label}_{needed[label]}.png (label={label})")
        needed[label] += 1

if all(v >= 2 for v in needed.values()):
    print("Done!")