# Actor-Critic 簡化版：使用折扣回報與價值估計的差值作為優勢
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributions as distributions
import numpy as np

class ActorCriticAgent:
    """Actor-Critic 智能體（簡化版），使用 G_t - V(s_t) 作為優勢"""
    def __init__(self, env):
        self.action_n = env.action_space.n
        self.gamma = 0.99
        
        # Actor 網路：輸出 Softmax 動作機率
        self.actor_net = self.build_net(
            input_size=env.observation_space.shape[0],
            hidden_sizes=[],
            output_size=self.action_n,
            output_activator=nn.Softmax(dim=1)
        )
        
        # Critic 網路：輸出單一數值 V(s) 作為狀態價值估計
        self.critic_net = self.build_net(
            input_size=env.observation_space.shape[0],
            hidden_sizes=[],
            output_size=1
        )
        
        self.actor_optimizer = optim.Adam(self.actor_net.parameters(), lr=0.005)
        self.critic_optimizer = optim.Adam(self.critic_net.parameters(), lr=0.005)

    def build_net(self, input_size, hidden_sizes, output_size, output_activator=None, use_bias=False):
        layers = []
        for input_size, output_size in zip(
                [input_size] + hidden_sizes, hidden_sizes + [output_size]):
            layers.append(nn.Linear(input_size, output_size, bias=use_bias))
            layers.append(nn.ReLU())
        layers = layers[:-1]
        if output_activator:
            layers.append(output_activator)
        model = nn.Sequential(*layers)
        return model

    def reset(self, mode=None):
        self.mode = mode
        if self.mode == 'train':
            self.trajectory = []

    def step(self, observation, reward, terminated):
        state_tensor = torch.as_tensor(observation, dtype=torch.float).unsqueeze(0)
        
        prob_tensor = self.actor_net(state_tensor)
        action_tensor = distributions.Categorical(prob_tensor).sample()
        action = action_tensor.item()
        
        if self.mode == 'train':
            # 記錄 Critic 的價值估計 V(s) 供後續計算優勢
            value_tensor = self.critic_net(state_tensor)
            self.trajectory += [observation, reward, terminated, action, value_tensor]
        
        return action

    def close(self):
        if self.mode == 'train':
            self.learn()

    def learn(self):
        """計算優勢 G_t - V(s_t)，同時更新 Actor 與 Critic"""
        # 將 trajectory 中的觀測轉為 numpy 再轉 tensor，避免梯度計算圖問題
        state_array = np.array(self.trajectory[0::5])
        state_tensor = torch.as_tensor(state_array, dtype=torch.float)

        reward_tensor = torch.as_tensor(self.trajectory[1::5], dtype=torch.float)
        action_tensor = torch.as_tensor(self.trajectory[3::5], dtype=torch.long)
        value_tensor = torch.cat(self.trajectory[4::5]).squeeze(1)

        # 計算折扣回報 G_t
        arange_tensor = torch.arange(state_tensor.shape[0], dtype=torch.float)
        discount_tensor = self.gamma ** arange_tensor
        discounted_reward_tensor = discount_tensor * reward_tensor
        discounted_return_tensor = discounted_reward_tensor.flip(0).cumsum(0).flip(0)

        # 優勢 = G_t - V(s_t)
        advantage_tensor = discounted_return_tensor - value_tensor

        # Actor 損失：最小化 -A_t log π(a_t|s_t)
        all_pi_tensor = self.actor_net(state_tensor)
        pi_tensor = torch.gather(all_pi_tensor, 1, action_tensor.unsqueeze(1)).squeeze(1)
        log_pi_tensor = torch.log(torch.clamp(pi_tensor, 1e-6, 1.))
        actor_loss = -(advantage_tensor * log_pi_tensor).mean()

        # Critic 損失：最小化 (G_t - V(s_t))²
        critic_loss = ((discounted_return_tensor - value_tensor) ** 2).mean()

        self.actor_optimizer.zero_grad()
        actor_loss.backward(retain_graph=True)
        self.actor_optimizer.step()

        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()
