# VPG (Vanilla Policy Gradient / REINFORCE)：使用折扣回報加權的完整回合策略梯度
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributions as distributions

class VPGAgent:
    """Vanilla Policy Gradient 智能體，直接使用折扣回報 G_t 更新策略"""
    def __init__(self, env):
        self.action_n = env.action_space.n
        self.gamma = 0.99
        self.policy_net = self.build_net(
            input_size=env.observation_space.shape[0],
            hidden_sizes=[],
            output_size=self.action_n,
            output_activator=nn.Softmax(dim=1)
        )
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=0.005)

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
        prob_tensor = self.policy_net(state_tensor)
        action_tensor = distributions.Categorical(prob_tensor).sample()
        action = action_tensor.numpy()[0]
        if self.mode == 'train':
            self.trajectory += [observation, reward, terminated, action]
        return action

    def close(self):
        if self.mode == 'train':
            self.learn()

    def learn(self):
        """REINFORCE 核心：計算 G_t，最小化 -G_t log π(a_t|s_t)"""
        state_tensor = torch.as_tensor(self.trajectory[0::4], dtype=torch.float)
        reward_tensor = torch.as_tensor(self.trajectory[1::4], dtype=torch.float)
        action_tensor = torch.as_tensor(self.trajectory[3::4], dtype=torch.long)
        # 計算折扣回報 G_t
        arange_tensor = torch.arange(state_tensor.shape[0], dtype=torch.float)
        discount_tensor = self.gamma ** arange_tensor
        discounted_reward_tensor = discount_tensor * reward_tensor
        discounted_return_tensor = discounted_reward_tensor.flip(0).cumsum(0).flip(0)
        # 取出實際動作的對數機率
        all_pi_tensor = self.policy_net(state_tensor)
        pi_tensor = torch.gather(all_pi_tensor, 1, action_tensor.unsqueeze(1)).squeeze(1)
        log_pi_tensor = torch.log(torch.clamp(pi_tensor, 1e-6, 1.))
        loss_tensor = -(discounted_return_tensor * log_pi_tensor).mean()
        self.optimizer.zero_grad()
        loss_tensor.backward()
        self.optimizer.step()
