import matplotlib.pyplot as plt
import numpy as np
import gd

# 資料點：y ≈ 2x + 2（加上一些雜訊）
x = np.array([0, 1, 2, 3, 4], dtype=np.float32)
y = np.array([1.9, 3.1, 3.9, 5.0, 6.2], dtype=np.float32)

"""線性預測函數：y_hat = a0 + a1 * x"""
def predict(a, xt):
	return a[0]+a[1]*xt

"""均方誤差（MSE）損失函數"""
def MSE(a, x, y):
	total = 0
	for i in range(len(x)):
		total += (y[i]-predict(a,x[i]))**2
	return total

def loss(p):
	return MSE(p, x, y)

# 從 (a0=0, a1=0) 開始梯度下降，擬合最佳直線
p = [0.0, 0.0]
plearn = gd.gradientDescendent(loss, p, max_loops=3000, dump_period=1)
# 繪製原始資料與擬合直線
y_predicted = list(map(lambda t: plearn[0]+plearn[1]*t, x))
print('y_predicted=', y_predicted)
plt.plot(x, y, 'ro', label='Original data')
plt.plot(x, y_predicted, label='Fitted line')
plt.legend()
plt.show()
