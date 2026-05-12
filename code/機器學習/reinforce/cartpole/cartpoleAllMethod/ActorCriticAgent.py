# Actor-Critic：同時學習策略（Actor）與價值函數（Critic）
# 使用 TD 誤差作為優勢函數更新策略
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributions as distributions

class ActorCriticAgent:
    """Actor-Critic 智能體，Actor 學習策略、Critic 估計狀態價值以降低方差"""
    def __init__(self, env):
        self.action_n = env.action_space.n
        self.gamma = 0.99
        
        # Actor 網路：狀態 → 動作機率分布
        self.actor_net = self.build_net(
            input_size=env.observation_space.shape[0],
            hidden_sizes=[64],
            output_size=self.action_n,
            output_activator=nn.Softmax(dim=1)
        )
        
        # Critic 網路：狀態 → 價值估計 V(s)
        self.critic_net = self.build_net(
            input_size=env.observation_space.shape[0],
            hidden_sizes=[64],
            output_size=1,
            output_activator=None
        )
        
        self.actor_optimizer = optim.Adam(self.actor_net.parameters(), lr=0.001)
        self.critic_optimizer = optim.Adam(self.critic_net.parameters(), lr=0.001)

    def build_net(self, input_size, hidden_sizes, output_size, output_activator=None, use_bias=True):
        """建立多層感知器，支援可選輸出激活函數"""
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
        """選擇動作，訓練模式下同時記錄 Critic 的價值估計"""
        state_tensor = torch.as_tensor(observation, dtype=torch.float).unsqueeze(0)
        
        prob_tensor = self.actor_net(state_tensor)
        action_tensor = distributions.Categorical(prob_tensor).sample()
        action = action_tensor.numpy()[0]
        
        if self.mode == 'train':
            # 取得當前狀態的價值估計 V(s)，用於後續計算 TD 誤差
            value = self.critic_net(state_tensor)
            self.trajectory += [observation, reward, terminated, action, value.detach().numpy()[0][0]]
        return action

    def close(self):
        if self.mode == 'train':
            self.learn()

    def learn(self):
        """使用 TD 誤差作為優勢函數更新 Actor，並用 MSE 更新 Critic"""
        state_tensor = torch.as_tensor(self.trajectory[0::5], dtype=torch.float)
        reward_tensor = torch.as_tensor(self.trajectory[1::5], dtype=torch.float)
        action_tensor = torch.as_tensor(self.trajectory[3::5], dtype=torch.long)
        value_tensor = torch.as_tensor(self.trajectory[4::5], dtype=torch.float)
        
        # 計算折扣回報 G_t
        arange_tensor = torch.arange(state_tensor.shape[0], dtype=torch.float)
        discount_tensor = self.gamma ** arange_tensor
        discounted_reward_tensor = discount_tensor * reward_tensor
        discounted_return_tensor = discounted_reward_tensor.flip(0).cumsum(0).flip(0)
        
        # 計算優勢函數 A_t = r_t + γV(s_{t+1}) - V(s_t) 即 TD 誤差
        next_value_tensor = torch.zeros_like(value_tensor)
        next_value_tensor[:-1] = value_tensor[1:]
        advantage_tensor = reward_tensor + self.gamma * next_value_tensor - value_tensor
        
        # Actor 損失：最小化 -A_t log π(a_t|s_t)
        all_pi_tensor = self.actor_net(state_tensor)
        pi_tensor = torch.gather(all_pi_tensor, 1, action_tensor.unsqueeze(1)).squeeze(1)
        log_pi_tensor = torch.log(torch.clamp(pi_tensor, 1e-6, 1.))
        actor_loss = -(advantage_tensor.detach() * log_pi_tensor).mean()
        
        # Critic 損失：最小化 (V(s_t) - G_t)²
        current_value_tensor = self.critic_net(state_tensor).squeeze()
        critic_loss = nn.MSELoss()(current_value_tensor, discounted_return_tensor.detach())
        
        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()
        
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()