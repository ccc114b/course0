import os
import random
import numpy as np
from tensor import Tensor
from nn import Adam
from gpt import GPT

random.seed(42)
np.random.seed(42)

# 1. 準備資料集
if not os.path.exists('input.txt'):
    import urllib.request
    names_url = 'https://raw.githubusercontent.com/karpathy/makemore/988aa59/names.txt'
    urllib.request.urlretrieve(names_url, 'input.txt')

docs = [line.strip() for line in open('input.txt') if line.strip()]
random.shuffle(docs)
print(f"num docs: {len(docs)}")

# 2. 字符級 Tokenizer
uchars = sorted(set(''.join(docs)))
BOS = len(uchars)
vocab_size = len(uchars) + 1
print(f"vocab size: {vocab_size}")

# 3. 初始化模型與優化器
block_size = 16
model = GPT(vocab_size=vocab_size, block_size=block_size, n_layer=1, n_embd=16, n_head=4)
params = model.parameters()
print(f"num params: {len(params)}")

optimizer = Adam(params, lr=0.01)

# 4. 訓練迴圈（向量化，一次計算整段序列）
num_steps = 1000

for step in range(num_steps):
    doc = docs[step % len(docs)]
    tokens = [BOS] + [uchars.index(ch) for ch in doc] + [BOS]
    n = min(block_size, len(tokens) - 1)
    
    # 準備批次輸入 (B=1, T=n)
    x = np.array([tokens[:n]], dtype=int)
    y = np.array([tokens[1:n+1]], dtype=int)
    
    optimizer.zero_grad()
    
    logits = model(x)                     # 前向傳播
    loss = logits.cross_entropy(y)        # 全序列一次計算損失
    
    loss.backward()                       # 反向傳播
    optimizer.step()                      # Adam 更新
    
    optimizer.lr = 0.01 * (1 - step / num_steps)  # 學習率線性衰減
    
    print(f"step {step+1:4d} / {num_steps:4d} | loss {loss.data:.4f}", end='\r')

# 5. 推論（自回歸生成）
print("\n--- inference (new, hallucinated names) ---")
temperature = 0.5

for sample_idx in range(20):
    idx = [BOS]
    for pos_id in range(block_size):
        x = np.array([idx], dtype=int)
        logits = model(x)
        last_logits = logits.data[0, -1, :]  # 取最後一步的 logits
        
        # Temperature Scaling + Softmax
        exps = np.exp(last_logits / temperature - np.max(last_logits / temperature))
        probs = exps / np.sum(exps)
        
        next_token = np.random.choice(range(vocab_size), p=probs)
        if next_token == BOS:
            break
        idx.append(next_token)
        
    sample = "".join([uchars[i] for i in idx[1:]])
    print(f"sample {sample_idx+1:2d}: {sample}")