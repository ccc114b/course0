import math
import numpy as np
from numpy.linalg import norm

"""
  數值微分：計算函數 f 在點 p 的第 k 個變數的偏導數。
  使用前向差分近似：df/dk ≈ (f(p + h*e_k) - f(p)) / h
"""
def df(f, p, k, h=0.01):
    p1 = p.copy()
    p1[k] = p[k]+h
    return (f(p1) - f(p)) / h

"""
  計算函數 f 在點 p 的梯度向量。
  對每個維度分別計算偏導數，組合成梯度向量。
"""
def grad(f, p, h=0.01):
    gp = p.copy()
    for k in range(len(p)):
        gp[k] = df(f, p, k, h)
    return gp

"""
  梯度下降法（Gradient Descent）：
    從初始點 p0 開始，沿梯度反方向逐步移動，
    直到梯度長度小於閾值或達到最大疊代次數。
  
  參數：
    f          — 目標函數
    p0         — 初始點
    h          — 學習率（步伐大小）
    max_loops  — 最大疊代次數
    dump_period — 輸出頻率（每多少步印一次狀態）
"""
def gradientDescendent(f, p0, h=0.01, max_loops=100000, dump_period=1000):
    np.set_printoptions(precision=6)
    p = p0.copy()
    for i in range(max_loops):
        fp = f(p)
        gp = grad(f, p)
        glen = norm(gp)  # 梯度向量的 L2 範數，衡量收斂程度
        if i%dump_period == 0: 
            print('{:05d}:f(p)={:.3f} p={:s} gp={:s} glen={:.5f}'.format(i, fp, str(p), str(gp), glen))
        if glen < 0.00001:  # 梯度接近零時停止（已找到極值點）
            break
        gh = np.multiply(gp, -1*h)  # 沿梯度反方向
        p += gh
    print('{:05d}:f(p)={:.3f} p={:s} gp={:s} glen={:.5f}'.format(i, fp, str(p), str(gp), glen))
    return p
