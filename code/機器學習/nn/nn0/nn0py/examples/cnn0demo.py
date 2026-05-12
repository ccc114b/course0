# cnn0demo.py — 使用 CNN 進行 MNIST 手寫數字分類訓練範例
import os
import gzip
import urllib.request
import random

from nn0 import Value, Adam, cross_entropy
from cnn0 import CNN

"""
  載入 MNIST 資料集。
  從 Google Cloud Storage 下載 gzip 壓縮的二進位檔案，
  解析圖片與標籤資料。
"""
def load_mnist_data():
    base_url = "https://storage.googleapis.com/cvdf-datasets/mnist/"
    files = {
        "train_img": "_data/train-images-idx3-ubyte.gz",
        "train_lbl": "_data/train-labels-idx1-ubyte.gz",
        "test_img": "_data/t10k-images-idx3-ubyte.gz",
        "test_lbl": "_data/t10k-labels-idx1-ubyte.gz",
    }

    for name, filename in files.items():
        if not os.path.exists(filename):
            print(f"正在下載 {filename} ...")
            urllib.request.urlretrieve(base_url + filename, filename)
            
    def read_images(filename):
        with gzip.open(filename, 'rb') as f: data = f.read()
        return data[16:] # 略過檔案標頭
        
    def read_labels(filename):
        with gzip.open(filename, 'rb') as f: data = f.read()
        return data[8:]  # 略過檔案標頭
        
    print("載入 MNIST 至記憶體中...")
    return (read_images(files["train_img"]), read_labels(files["train_lbl"]),
            read_images(files["test_img"]),  read_labels(files["test_lbl"]))

"""
  預處理 MNIST 影像：
    1. 從原始 28×28 使用 stride=2 降採樣為 14×14
    2. 像素值正規化至 [0, 1] 區間
    3. 封裝為 Value 節點
  回傳形狀為 (1, 14, 14) 的巢狀列表。
"""
def preprocess_image(raw_data, index):
    start = index * 784
    img_28 = raw_data[start:start+784]
    
    img_14 =[]
    for i in range(14):
        row =[]
        for j in range(14):
            val = img_28[(2*i)*28 + (2*j)]
            row.append(Value(val / 255.0))
        img_14.append(row)
        
    return [img_14] # 單通道 (1, 14, 14)

def main():
    X_train, y_train, X_test, y_test = load_mnist_data()
    
    model = CNN()
    optimizer = Adam(model.parameters(), lr=0.005)
    
    num_train = 1000   # 僅使用 1000 筆訓練資料（純 Python 效能限制）
    num_epochs = 5
    
    print(f"\n--- 開始訓練 (僅訓練 {num_train} 筆樣本，共 {num_epochs} Epochs) ---")
    
    for epoch in range(num_epochs):
        total_loss = 0.0
        correct = 0
        
        indices = list(range(num_train))
        random.shuffle(indices) # 每個 Epoch 隨機打亂順序
        
        for step, idx in enumerate(indices):
            x = preprocess_image(X_train, idx)
            y = y_train[idx]
            
            logits = model(x)           # 前向傳播
            loss = cross_entropy(logits, y)  # 交叉熵損失
            
            # 計算預測類別
            pred = max(range(10), key=lambda i: logits[i].data)
            if pred == y:
                correct += 1
            
            loss.backward()  # 反向傳播
            optimizer.step() # Adam 參數更新
            
            total_loss += loss.data
            
            if (step + 1) % 20 == 0:
                print(f"Epoch {epoch+1}, Step {step+1:3d}/{num_train}, Loss: {loss.data:.4f}")
                
        acc = correct / num_train * 100
        avg_loss = total_loss / num_train
        print(f"→ Epoch {epoch+1} 總結: 平均 Loss: {avg_loss:.4f}, 準確率: {acc:.2f}%\n")
        
    # 測試階段
    num_test = 50
    print(f"--- 測試階段 (抽取 {num_test} 筆測試樣本) ---")
    correct = 0
    for idx in range(num_test):
        x = preprocess_image(X_test, idx)
        y = y_test[idx]
        
        logits = model(x)
        pred = max(range(10), key=lambda i: logits[i].data)
        if pred == y:
            correct += 1
            
    print(f"測試準確率: {correct / num_test * 100:.2f}%")

if __name__ == '__main__':
    main()