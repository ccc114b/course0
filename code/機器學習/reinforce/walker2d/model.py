# Actor-Critic 模型與 RunningMeanStd 狀態歸一化，用於 PPO 訓練 Walker2d
import torch
import torch.nn as nn
from torch.distributions import Normal
import numpy as np

class RunningMeanStd:
    """線上計算串流資料的均值與變異數（Welford 演算法），用於狀態歸一化"""
    def __init__(self, shape):
        self.mean = np.zeros(shape, dtype=np.float32)
        self.var = np.ones(shape, dtype=np.float32)
        self.count = 1e-4

    def update(self, x):
        batch_mean = np.mean(x, axis=0)
        batch_var = np.var(x, axis=0)
        batch_count = x.shape[0]
        self.update_from_moments(batch_mean, batch_var, batch_count)

    def update_from_moments(self, batch_mean, batch_var, batch_count):
        """使用 Welford 演算法合併批次統計到全域統計"""
        delta = batch_mean - self.mean
        tot_count = self.count + batch_count
        new_mean = self.mean + delta * batch_count / tot_count
        m_a = self.var * self.count
        m_b = batch_var * batch_count
        M2 = m_a + m_b + np.square(delta) * self.count * batch_count / tot_count
        new_var = M2 / tot_count
        self.mean, self.var, self.count = new_mean, new_var, tot_count

class ActorCritic(nn.Module):
    """PPO 的 Actor-Critic 網路，Actor 輸出高斯分布均值，log_std 為可學習參數"""
    def __init__(self, state_dim, action_dim):
        super(ActorCritic, self).__init__()
        # Actor：兩層 256 維隱藏層 + Tanh 確保輸出在 [-1, 1]
        self.actor = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim),
            nn.Tanh()
        )
        # Critic：兩層 256 維隱藏層，輸出單一狀態價值 V(s)
        self.critic = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )
        # 可學習的對數標準差，所有狀態共享同一 σ
        self.log_std = nn.Parameter(torch.zeros(1, action_dim))

    def get_action(self, state):
        """從高斯策略抽樣取得動作，回傳動作與對數機率"""
        mu = self.actor(state)
        std = torch.exp(self.log_std)
        dist = Normal(mu, std)
        action = dist.sample()
        return action, dist.log_prob(action).sum(axis=-1)

    def evaluate(self, state, action):
        """評估給定 (s, a) 的對數機率、價值與熵"""
        mu = self.actor(state)
        std = torch.exp(self.log_std)
        dist = Normal(mu, std)
        return dist.log_prob(action).sum(axis=-1), self.critic(state), dist.entropy().sum(axis=-1)
