import numpy as np
from tensor import Tensor
from nn import Module, Linear, Embedding, RMSNorm

"""
  因果自注意力（Causal Self-Attention）。
  每個位置只能關注自己和之前的 token（透過上三角矩陣遮蔽未來）。
  支援批次與多頭注意力計算。
"""
class CausalSelfAttention(Module):
    def __init__(self, n_embd, n_head):
        self.n_head = n_head
        self.head_dim = n_embd // n_head
        
        self.wq = Linear(n_embd, n_embd)
        self.wk = Linear(n_embd, n_embd)
        self.wv = Linear(n_embd, n_embd)
        self.wo = Linear(n_embd, n_embd)

    def __call__(self, x):
        B, T, C = x.data.shape
        
        # 將 Q、K、V 重塑為多頭形式 (B, nh, T, hs)
        q = self.wq(x).reshape(B, T, self.n_head, self.head_dim).transpose(1, 2)
        k = self.wk(x).reshape(B, T, self.n_head, self.head_dim).transpose(1, 2)
        v = self.wv(x).reshape(B, T, self.n_head, self.head_dim).transpose(1, 2)

        # Scaled Dot-Product Attention
        attn_logits = (q @ k.transpose(-2, -1)) * (self.head_dim ** -0.5)
        
        # 因果遮蔽（上三角矩陣，禁止看到未來）
        mask = np.triu(np.ones((T, T)), k=1) == 1
        attn_logits = attn_logits.masked_fill(mask, float('-inf'))
        
        attn_weights = attn_logits.softmax(axis=-1)
        
        out = attn_weights @ v
        out = out.transpose(1, 2).reshape(B, T, C)
        return self.wo(out)

"""
  前饋神經網路：FC1 (4x 維度) → ReLU → FC2 (恢復維度)
"""
class MLP(Module):
    def __init__(self, n_embd):
        self.fc1 = Linear(n_embd, 4 * n_embd)
        self.fc2 = Linear(4 * n_embd, n_embd)

    def __call__(self, x):
        return self.fc2(self.fc1(x).relu())

"""Transformer Block：Attention → MLP（含 Pre-LN 與殘差連接）"""
class Block(Module):
    def __init__(self, n_embd, n_head):
        self.attn = CausalSelfAttention(n_embd, n_head)
        self.mlp = MLP(n_embd)
        self.ln1 = RMSNorm(n_embd)
        self.ln2 = RMSNorm(n_embd)

    def __call__(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x

"""GPT 語言模型：Embedding → N×Block → LN → lm_head"""
class GPT(Module):
    def __init__(self, vocab_size, block_size, n_layer=1, n_embd=16, n_head=4):
        self.block_size = block_size
        self.wte = Embedding(vocab_size, n_embd)
        self.wpe = Embedding(block_size, n_embd)
        self.blocks = [Block(n_embd, n_head) for _ in range(n_layer)]
        self.ln_f = RMSNorm(n_embd)
        self.lm_head = Linear(n_embd, vocab_size)

    def __call__(self, idx):
        B, T = idx.shape
        pos = np.arange(0, T, dtype=int)
        
        tok_emb = self.wte(idx)       # (B, T, C)
        pos_emb = self.wpe(pos)       # (T, C)，會透過 broadcast 加到所有 batch
        x = tok_emb + pos_emb
        
        for block in self.blocks:
            x = block(x)
            
        x = self.ln_f(x)
        logits = self.lm_head(x)
        return logits