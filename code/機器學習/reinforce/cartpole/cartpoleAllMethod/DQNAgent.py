# DQN (Deep Q-Network)：使用深度網路逼近 Q 函數，含目標網路與經驗回放
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
import copy
import pandas as pd

class Replayer:
    """經驗回放緩衝區，使用 Pandas DataFrame 儲存轉移"""
    def __init__(self, capacity):
        self.memory = pd.DataFrame(index=range(capacity),
                columns=['state', 'action', 'reward', 'next_state', 'terminated'])
        self.i = 0
        self.count = 0
        self.capacity = capacity

    def store(self, *args):
        """儲存一筆轉移 (s, a, r, s', terminated)"""
        self.memory.loc[self.i] = np.asarray(args, dtype=object)
        self.i = (self.i + 1) % self.capacity
        self.count = min(self.count + 1, self.capacity)

    def sample(self, size):
        """隨機抽樣一批轉移"""
        indices = np.random.choice(self.count, size=size)
        return (np.stack(self.memory.loc[indices, field]) for field in
                self.memory.columns)

class DQNAgent:
    """Deep Q-Network 智能體，使用目標網路穩定訓練"""
    def __init__(self, env):
        self.action_n = env.action_space.n
        self.gamma = 0.99

        self.replayer = Replayer(10000)

        # 評估網路：當前學習的 Q 函數
        self.evaluate_net = self.build_net(
                input_size=env.observation_space.shape[0],
                hidden_sizes=[64, 64], output_size=self.action_n)
        self.optimizer = optim.Adam(self.evaluate_net.parameters(), lr=0.001)
        self.loss = nn.MSELoss()

    def build_net(self, input_size, hidden_sizes, output_size):
        layers = []
        for input_size, output_size in zip(
                [input_size,] + hidden_sizes, hidden_sizes + [output_size,]):
            layers.append(nn.Linear(input_size, output_size))
            layers.append(nn.ReLU())
        layers = layers[:-1]
        model = nn.Sequential(*layers)
        return model

    def reset(self, mode=None):
        self.mode = mode
        if self.mode == 'train':
            self.trajectory = []
            # 每個回合開始時複製評估網路作為目標網路
            self.target_net = copy.deepcopy(self.evaluate_net)

    def step(self, observation, reward, terminated):
        """ε-greedy 策略選擇動作，訓練模式下存入回放緩衝區"""
        if self.mode == 'train' and np.random.rand() < 0.001:
            action = np.random.randint(self.action_n)
        else:
            state_tensor = torch.as_tensor(observation,
                    dtype=torch.float).squeeze(0)
            q_tensor = self.evaluate_net(state_tensor)
            action_tensor = torch.argmax(q_tensor)
            action = action_tensor.item()
        if self.mode == 'train':
            self.trajectory += [observation, reward, terminated, action]
            # 每 4 步組合一筆完整轉移存入緩衝區
            if len(self.trajectory) >= 8:
                state, _, _, act, next_state, reward, terminated, _ = \
                        self.trajectory[-8:]
                self.replayer.store(state, act, reward, next_state, terminated)
            # 緩衝區累積 95% 後開始學習
            if self.replayer.count >= self.replayer.capacity * 0.95:
                self.learn()
        return action

    def close(self):
        pass

    def learn(self):
        """從回放緩衝區抽樣，計算 TD 目標並更新 Q 網路"""
        states, actions, rewards, next_states, terminateds = \
                self.replayer.sample(1024)
        state_tensor = torch.as_tensor(states, dtype=torch.float)
        action_tensor = torch.as_tensor(actions, dtype=torch.long)
        reward_tensor = torch.as_tensor(rewards, dtype=torch.float)
        next_state_tensor = torch.as_tensor(next_states, dtype=torch.float)
        terminated_tensor = torch.as_tensor(terminateds, dtype=torch.float)

        # 使用目標網路計算 max_{a'} Q_target(s', a')
        next_q_tensor = self.target_net(next_state_tensor)
        next_max_q_tensor, _ = next_q_tensor.max(axis=-1)
        # TD 目標：y = r + γ max_{a'} Q_target(s', a') (終止時無未來回報)
        target_tensor = reward_tensor + self.gamma * \
                (1. - terminated_tensor) * next_max_q_tensor
        pred_tensor = self.evaluate_net(state_tensor)
        # 取出實際執行動作 a 對應的 Q 值 Q(s,a)
        q_tensor = pred_tensor.gather(1, action_tensor.unsqueeze(1)).squeeze(1)
        loss_tensor = self.loss(target_tensor, q_tensor)
        self.optimizer.zero_grad()
        loss_tensor.backward()
        self.optimizer.step()

