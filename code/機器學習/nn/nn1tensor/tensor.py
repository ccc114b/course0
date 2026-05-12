import numpy as np

"""
  處理 NumPy 廣播機制在反向傳播時的梯度還原。
  當形狀不相符時，需要在廣播的維度上求和以匹配原始形狀。
"""
def unbroadcast(grad, shape):
    if grad.shape == shape:
        return grad
    ndim_diff = grad.ndim - len(shape)
    if ndim_diff > 0:
        grad = grad.sum(axis=tuple(range(ndim_diff)))
    for i, dim in enumerate(shape):
        if dim == 1 and grad.shape[i] > 1:
            grad = grad.sum(axis=i, keepdims=True)
    return grad

class Tensor:
    """
    自動微分張量，基於 NumPy 陣列。
    支援加法、乘法、矩陣乘法、形狀變換、激活函數等運算，
    並透過計算圖自動計算梯度。
    """
    def __init__(self, data, _children=(), requires_grad=False):
        self.data = np.array(data, dtype=np.float32)
        self.grad = np.zeros_like(self.data)
        self._backward = lambda: None  # 反向傳播函數（由運算設定）
        self._prev = set(_children)    # 計算圖中的父節點
        self.requires_grad = requires_grad

    def zero_grad(self):
        self.grad = np.zeros_like(self.data)

    """
      反向傳播：
        1. 拓樸排序（子節點先於父節點）
        2. 設定輸出梯度為全 1
        3. 逆序執行每個節點的 _backward
    """
    def backward(self):
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)
        build_topo(self)
        
        self.grad = np.ones_like(self.data)
        for v in reversed(topo):
            v._backward()

    # --- 基礎運算 ---

    # 加法：z = x + y，梯度還原至 x 與 y 的原始形狀（處理廣播）
    def __add__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data + other.data, (self, other), self.requires_grad or other.requires_grad)
        def _backward():
            self.grad += unbroadcast(out.grad, self.data.shape)
            other.grad += unbroadcast(out.grad, other.data.shape)
        out._backward = _backward
        return out

    # 乘法：z = x * y，梯度 = out.grad * other
    def __mul__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data * other.data, (self, other), self.requires_grad or other.requires_grad)
        def _backward():
            self.grad += unbroadcast(out.grad * other.data, self.data.shape)
            other.grad += unbroadcast(out.grad * self.data, other.data.shape)
        out._backward = _backward
        return out

    # 矩陣乘法：z = x @ y，梯度 = grad @ y^T 和 x^T @ grad
    def __matmul__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data @ other.data, (self, other), self.requires_grad or other.requires_grad)
        def _backward():
            self.grad += unbroadcast(out.grad @ np.swapaxes(other.data, -1, -2), self.data.shape)
            other.grad += unbroadcast(np.swapaxes(self.data, -1, -2) @ out.grad, other.data.shape)
        out._backward = _backward
        return out

    # --- 張量形狀操作 ---

    def transpose(self, ax1, ax2):
        out = Tensor(np.swapaxes(self.data, ax1, ax2), (self,), self.requires_grad)
        def _backward():
            self.grad += np.swapaxes(out.grad, ax1, ax2)
        out._backward = _backward
        return out

    def reshape(self, *shape):
        out = Tensor(self.data.reshape(*shape), (self,), self.requires_grad)
        def _backward():
            self.grad += out.grad.reshape(self.data.shape)
        out._backward = _backward
        return out

    # --- 激活與非線性函數 ---

    # ReLU：y = max(0, x)，梯度 = grad * (x > 0)
    def relu(self):
        out = Tensor(np.maximum(0, self.data), (self,), self.requires_grad)
        def _backward():
            self.grad += out.grad * (self.data > 0)
        out._backward = _backward
        return out

    # 遮蔽填充：用於 Attention 的因果遮蔽，遮罩處梯度為 0
    def masked_fill(self, mask, value):
        out_data = np.where(mask, value, self.data)
        out = Tensor(out_data, (self,), self.requires_grad)
        def _backward():
            self.grad += np.where(mask, 0, out.grad)
        out._backward = _backward
        return out

    """
      Softmax（數值穩定版本）：
        1. 減去最大值防止溢位
        2. 計算 e^(x - max) / Σ e^(x - max)
      
      反向傳播使用 Jacobian-vector product：
        dx_i = s_i * (dg_i - Σ(dg_j * s_j))
    """
    def softmax(self, axis=-1):
        max_val = np.max(self.data, axis=axis, keepdims=True)
        exps = np.exp(self.data - max_val)
        probs = exps / np.sum(exps, axis=axis, keepdims=True)
        out = Tensor(probs, (self,), self.requires_grad)
        def _backward():
            s = out.data
            grad_s = out.grad
            self.grad += s * (grad_s - np.sum(grad_s * s, axis=axis, keepdims=True))
        out._backward = _backward
        return out

    """
      交叉熵損失（融合 Softmax）：
        前向：先做 softmax，再對目標類別的機率取負對數
        反向：d_logits = (probs - one_hot(target)) / (B * T)
    """
    def cross_entropy(self, targets):
        logits = self.data
        max_logits = np.max(logits, axis=-1, keepdims=True)
        exps = np.exp(logits - max_logits)
        probs = exps / np.sum(exps, axis=-1, keepdims=True)
        
        batch_size, seq_len = targets.shape
        loss = 0.0
        for b in range(batch_size):
            for t in range(seq_len):
                loss -= np.log(probs[b, t, targets[b, t]] + 1e-10)
        loss = loss / (batch_size * seq_len)
        
        out = Tensor(loss, (self,), self.requires_grad)
        def _backward():
            d_logits = probs.copy()
            for b in range(batch_size):
                for t in range(seq_len):
                    d_logits[b, t, targets[b, t]] -= 1
            d_logits = d_logits / (batch_size * seq_len)
            self.grad += out.grad * d_logits
        out._backward = _backward
        return out

    # Python Magic Methods
    def __sub__(self, other): return self + (other * -1)
    def __truediv__(self, other): return self * (other ** -1)
    def __radd__(self, other): return self + other
    def __rmul__(self, other): return self * other
    def __pow__(self, power):
        out = Tensor(self.data ** power, (self,), self.requires_grad)
        def _backward():
            self.grad += out.grad * (power * self.data ** (power - 1))
        out._backward = _backward
        return out
