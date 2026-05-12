import numpy as np
from PIL import Image, ImageOps
from torchvision import datasets

def preprocess(img):
    """預處理：縮放至 20×20 灰階，歸一化至 [0,1]"""
    img = img.resize((20, 20))
    img = ImageOps.grayscale(img)
    arr = np.array(img) / 255.0
    return arr

def extract_features(arr):
    """從 20×20 影像提取 9 維特徵向量
    
    包含區域密度（8維）、全域密度（1維）、分散度（2維）
    """
    features = []
    
    h, w = 20, 20
    for i in range(4):
        row_sum = np.sum(arr[i*5:(i+1)*5, :], axis=0)
        features.extend([np.sum(row_sum > 0) / 20])
        col_sum = np.sum(arr[:, i*5:(i+1)*5], axis=1)
        features.extend([np.sum(col_sum > 0) / 20])
    
    features.append(np.sum(arr > 0.5) / (20 * 20))
    
    cy, cx = np.where(arr > 0.5)
    if len(cy) > 0:
        features.append(np.std(cy) / 10)
        features.append(np.std(cx) / 10)
    else:
        features.extend([0, 0])
    
    return np.array(features)

def load_templates():
    """從 MNIST 訓練集建立各數字的特徵模板（每類平均）"""
    transform = datasets.MNIST(root="./data", train=True, download=True)
    templates = {i: [] for i in range(10)}
    
    counts = {i: 3 for i in range(10)}
    for img, label in transform:
        if counts[label] > 0:
            arr = preprocess(img)
            feat = extract_features(arr)
            templates[label].append(feat)
            counts[label] -= 1
    
    for i in range(10):
        templates[i] = np.mean(templates[i], axis=0)
    
    return templates

def predict(image_path, templates):
    """最近鄰分類：計算歐氏距離匹配最相似的模板"""
    img = Image.open(image_path)
    arr = preprocess(img)
    feat = extract_features(arr)
    
    best_match = 0
    best_digit = -1
    
    for digit in range(10):
        dist = np.sum((feat - templates[digit]) ** 2)
        if dist < best_match or best_digit == -1:
            best_match = dist
            best_digit = digit
    
    print(f"Predicted: {best_digit}")
    return best_digit

if __name__ == "__main__":
    import sys
    
    print("Loading templates...")
    templates = load_templates()
    
    if len(sys.argv) > 1:
        predict(sys.argv[1], templates)
    else:
        print("Usage: python digit_classical.py <image_path>")