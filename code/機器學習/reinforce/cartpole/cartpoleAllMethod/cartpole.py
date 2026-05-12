# CartPole 強化學習整合測試腳本：可載入不同 Agent 進行訓練與評估
import sys
import logging
import itertools
import numpy as np
np.random.seed(0)
import pandas as pd
import gymnasium as gym
import matplotlib.pyplot as plt

# 設定 logging 輸出格式
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    stream=sys.stdout, datefmt='%H:%M:%S')

# 建立 CartPole 環境，確認環境資訊
env = gym.make('CartPole-v1')

for key in vars(env):
    logging.info('%s: %s', key, vars(env)[key])
for key in vars(env.spec):
    logging.info('%s: %s', key, vars(env.spec)[key])

# 匯入所有可用的 Agent
from VPGAgent import VPGAgent
from VPGwBaselineAgent import VPGwBaselineAgent
from DQNAgent import DQNAgent
from SARSAAgent import SARSAAgent
from ActorCriticAgent import ActorCriticAgent

# 選擇要使用的 Agent（取消註解即可切換）
# agent = VPGAgent(env)
# agent = VPGwBaselineAgent(env)
# agent = DQNAgent(env)
agent = SARSAAgent(env)
# agent = ActorCriticAgent(env)

def play_episode(env, agent, seed=None, mode=None, render=False):
    """在環境中執行一個完整回合，支援訓練與渲染模式"""
    observation, info = env.reset(seed=seed)
    reward, terminated, truncated = 0., False, False
    agent.reset(mode=mode)
    episode_reward, elapsed_steps = 0., 0
    while True:
        action = agent.step(observation, reward, terminated)
        if render:
            env.render()
        if terminated or truncated:
            break
        observation, reward, terminated, truncated, info = env.step(action)
        episode_reward += reward
        elapsed_steps += 1
    agent.close()
    return episode_reward, elapsed_steps

# ── 訓練階段 ──────────────────────────────
logging.info('==== train ====')
episode_rewards = []
for episode in itertools.count():
    episode_reward, elapsed_steps = play_episode(env, agent, seed=episode, mode='train')
    episode_rewards.append(episode_reward)
    logging.info('train episode %d: reward = %.2f, steps = %d',
                 episode, episode_reward, elapsed_steps)
    # 最近 20 回合平均報酬接近最大步數時停止
    if np.mean(episode_rewards[-20:]) > env.spec.max_episode_steps - 10:
        break

# 繪製訓練過程的報酬曲線
plt.plot(episode_rewards)
plt.xlabel('Episodes')
plt.ylabel('Episode Reward')
plt.title('Training Rewards')
plt.show()

# ── 測試階段 ──────────────────────────────
logging.info('==== test ====')
episode_rewards = []
for episode in range(100):
    episode_reward, elapsed_steps = play_episode(env, agent)
    episode_rewards.append(episode_reward)
    logging.info('test episode %d: reward = %.2f, steps = %d',
                 episode, episode_reward, elapsed_steps)

logging.info('average episode reward = %.2f ± %.2f',
             np.mean(episode_rewards), np.std(episode_rewards))

# ── 渲染展示 ──────────────────────────────
env = gym.make('CartPole-v1', render_mode="human")
episode_reward, elapsed_steps = play_episode(env, agent, render=True)
env.close()
