"""
Breakout DQN Trainer
====================
使用 Deep Q-Network (DQN) 訓練 Atari Breakout

依賴安裝：
    pip install torch torchvision gymnasium[atari] ale-py opencv-python

用法：
    python train.py                        # 從頭開始訓練
    python train.py --resume checkpoints/  # 從 checkpoint 繼續訓練
    python train.py --episodes 2000        # 自訂訓練回合數
"""

import os
import math
import random
import argparse
import time
from collections import deque, namedtuple
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import ale_py
import gymnasium as gym
from gymnasium.wrappers import (
    AtariPreprocessing,
    FrameStackObservation,
)
gym.register_envs(ale_py)   # 註冊 ALE/Breakout 等 Atari 環境

# ─────────────────────────────────────────
#  超參數
# ─────────────────────────────────────────
DEVICE = torch.device(
    "cuda"  if torch.cuda.is_available() else
    "mps"   if torch.backends.mps.is_available() else
    "cpu"
)

FRAME_SKIP        = 4          # 每個 action 重複幾幀
STACK_SIZE        = 4          # 疊幾幀餵給網路
IMG_SIZE          = 84         # 縮放後的圖像尺寸

BATCH_SIZE        = 32
REPLAY_CAPACITY   = 100_000    # 經驗回放池大小（顯存吃緊可調低）
MIN_REPLAY        = 10_000     # 至少累積多少筆才開始訓練
GAMMA             = 0.99       # 折扣因子
LR                = 1e-4       # Adam 學習率
TARGET_UPDATE     = 1_000      # 每多少步同步 target network
GRAD_CLIP         = 10.0       # gradient clipping

EPS_START         = 1.0        # ε-greedy 初始探索率
EPS_END           = 0.05       # 最低探索率
EPS_DECAY_STEPS   = 500_000    # 探索率衰減步數

SAVE_EVERY        = 100        # 每多少 episode 存一次 checkpoint
LOG_EVERY         = 10         # 每多少 episode 印一次 log

# ─────────────────────────────────────────
#  Experience Replay
# ─────────────────────────────────────────
Transition = namedtuple("Transition", ["state", "action", "reward", "next_state", "done"])


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.buffer: deque = deque(maxlen=capacity)

    def push(self, *args):
        self.buffer.append(Transition(*args))

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        return Transition(*zip(*batch))

    def __len__(self):
        return len(self.buffer)


# ─────────────────────────────────────────
#  DQN 網路（Nature DQN 架構）
# ─────────────────────────────────────────
class DQN(nn.Module):
    """
    Nature DQN (Mnih et al., 2015)
    Input:  (B, 4, 84, 84) — 4 幀灰階影像
    Output: (B, n_actions) — 每個動作的 Q 值
    """
    def __init__(self, n_actions: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(STACK_SIZE, 32, kernel_size=8, stride=4),  # → 20x20
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),           # → 9x9
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),           # → 7x7
            nn.ReLU(),
        )
        conv_out = 64 * 7 * 7  # = 3136
        self.fc = nn.Sequential(
            nn.Linear(conv_out, 512),
            nn.ReLU(),
            nn.Linear(512, n_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, 4, 84, 84), dtype=float32, range [0,1]
        x = self.conv(x)
        x = x.flatten(start_dim=1)
        return self.fc(x)


# ─────────────────────────────────────────
#  環境包裝器
# ─────────────────────────────────────────
def make_env(render: bool = False) -> gym.Env:
    render_mode = "human" if render else "rgb_array"
    env = gym.make("ALE/Breakout-v5", render_mode=render_mode, frameskip=1)
    env = AtariPreprocessing(
        env,
        noop_max=30,
        frame_skip=FRAME_SKIP,
        screen_size=IMG_SIZE,
        grayscale_obs=True,
        grayscale_newaxis=False,
        scale_obs=True,          # 縮放到 [0,1]
    )
    env = FrameStackObservation(env, stack_size=STACK_SIZE)
    return env


def obs_to_tensor(obs) -> torch.Tensor:
    """將 gymnasium observation 轉為 (1, 4, 84, 84) float32 tensor"""
    arr = np.array(obs, dtype=np.float32)   # (4, 84, 84)
    return torch.from_numpy(arr).unsqueeze(0).to(DEVICE)


# ─────────────────────────────────────────
#  ε-greedy 策略
# ─────────────────────────────────────────
def get_epsilon(step: int) -> float:
    # 線性衰減
    progress = min(step / EPS_DECAY_STEPS, 1.0)
    return EPS_START + (EPS_END - EPS_START) * progress


@torch.no_grad()
def select_action(state: torch.Tensor, policy_net: DQN, epsilon: float, n_actions: int) -> int:
    if random.random() < epsilon:
        return random.randrange(n_actions)
    q = policy_net(state)
    return q.argmax(dim=1).item()


# ─────────────────────────────────────────
#  訓練一個 mini-batch
# ─────────────────────────────────────────
def optimize(
    policy_net: DQN,
    target_net: DQN,
    optimizer: optim.Optimizer,
    replay: ReplayBuffer,
) -> float:
    if len(replay) < BATCH_SIZE:
        return 0.0

    batch = replay.sample(BATCH_SIZE)

    states      = torch.from_numpy(np.array(batch.state,      dtype=np.float32)).to(DEVICE)
    next_states = torch.from_numpy(np.array(batch.next_state, dtype=np.float32)).to(DEVICE)
    actions     = torch.tensor(batch.action, dtype=torch.long,  device=DEVICE).unsqueeze(1)
    rewards     = torch.tensor(batch.reward, dtype=torch.float32, device=DEVICE)
    dones       = torch.tensor(batch.done,   dtype=torch.float32, device=DEVICE)

    # Q(s, a)
    q_values = policy_net(states).gather(1, actions).squeeze(1)

    # r + γ * max_a' Q_target(s', a')  （終止狀態不加未來獎勵）
    with torch.no_grad():
        max_next_q = target_net(next_states).max(dim=1).values
        targets = rewards + GAMMA * max_next_q * (1 - dones)

    loss = F.smooth_l1_loss(q_values, targets)

    optimizer.zero_grad()
    loss.backward()
    nn.utils.clip_grad_norm_(policy_net.parameters(), GRAD_CLIP)
    optimizer.step()

    return loss.item()


# ─────────────────────────────────────────
#  主訓練迴圈
# ─────────────────────────────────────────
def train(args):
    print(f"[Device] {DEVICE}")
    os.makedirs(args.checkpoint_dir, exist_ok=True)

    env = make_env()
    n_actions = env.action_space.n
    print(f"[Env] Action space: {n_actions} actions")

    policy_net = DQN(n_actions).to(DEVICE)
    target_net = DQN(n_actions).to(DEVICE)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=LR)
    replay    = ReplayBuffer(REPLAY_CAPACITY)

    global_step = 0
    start_episode = 0
    best_reward = -float("inf")

    # ── 從 checkpoint 繼續 ──
    if args.resume:
        ckpts = sorted(
            [f for f in os.listdir(args.resume) if f.endswith(".pt") and "_ep" in f],
            key=lambda f: int(f.split("_ep")[1].split(".")[0])
        )
        if ckpts:
            ckpt_path = os.path.join(args.resume, ckpts[-1])
            print(f"[Resume] Loading {ckpt_path}")
            ckpt = torch.load(ckpt_path, map_location=DEVICE, weights_only=False)
            policy_net.load_state_dict(ckpt["policy_net"])
            target_net.load_state_dict(ckpt["target_net"])
            optimizer.load_state_dict(ckpt["optimizer"])
            global_step    = ckpt.get("global_step", 0)
            start_episode  = ckpt.get("episode", 0)
            best_reward    = ckpt.get("best_reward", -float("inf"))
            print(f"[Resume] ep={start_episode}, step={global_step}, best={best_reward:.1f}")

    rewards_history = deque(maxlen=100)
    t0 = time.time()

    for episode in range(start_episode, args.episodes):
        obs, _ = env.reset()
        state  = np.array(obs, dtype=np.float32)
        ep_reward = 0.0

        while True:
            epsilon = get_epsilon(global_step)
            state_t = torch.from_numpy(state).unsqueeze(0).to(DEVICE)
            action  = select_action(state_t, policy_net, epsilon, n_actions)

            next_obs, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            next_state = np.array(next_obs, dtype=np.float32)

            # 裁切 reward 到 [-1, 1]
            clipped_reward = float(np.clip(reward, -1, 1))

            replay.push(state, action, clipped_reward, next_state, float(done))
            state = next_state
            ep_reward += reward
            global_step += 1

            # ── 訓練 ──
            if len(replay) >= MIN_REPLAY:
                optimize(policy_net, target_net, optimizer, replay)

            # ── 同步 target network ──
            if global_step % TARGET_UPDATE == 0:
                target_net.load_state_dict(policy_net.state_dict())

            if done:
                break

        rewards_history.append(ep_reward)
        avg_100 = np.mean(rewards_history)

        # ── 儲存最佳模型 ──
        if avg_100 > best_reward and len(rewards_history) == 100:
            best_reward = avg_100
            torch.save(policy_net.state_dict(),
                       os.path.join(args.checkpoint_dir, "best_model.pt"))

        # ── 定期 checkpoint ──
        if (episode + 1) % SAVE_EVERY == 0:
            ckpt_path = os.path.join(
                args.checkpoint_dir, f"dqn_ep{episode+1}.pt"
            )
            torch.save({
                "episode":     episode + 1,
                "global_step": global_step,
                "policy_net":  policy_net.state_dict(),
                "target_net":  target_net.state_dict(),
                "optimizer":   optimizer.state_dict(),
                "best_reward": best_reward,
            }, ckpt_path)
            print(f"  → Saved checkpoint: {ckpt_path}")

        # ── Log ──
        if (episode + 1) % LOG_EVERY == 0:
            elapsed = time.time() - t0
            eps = get_epsilon(global_step)
            print(
                f"Ep {episode+1:6d} | "
                f"Reward {ep_reward:7.1f} | "
                f"Avg100 {avg_100:7.2f} | "
                f"ε {eps:.4f} | "
                f"Steps {global_step:,} | "
                f"Buffer {len(replay):,} | "
                f"Time {elapsed/60:.1f}min"
            )

    env.close()
    print("\n訓練完成！")
    print(f"最佳 100-ep 平均獎勵：{best_reward:.2f}")
    print(f"最佳模型：{os.path.join(args.checkpoint_dir, 'best_model.pt')}")


# ─────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train DQN on Breakout")
    parser.add_argument("--episodes",        type=int,  default=3000,
                        help="訓練回合數 (default: 3000)")
    parser.add_argument("--checkpoint-dir",  type=str,  default="checkpoints",
                        help="checkpoint 儲存資料夾 (default: checkpoints)")
    parser.add_argument("--resume",          type=str,  default=None,
                        help="從指定資料夾的最新 checkpoint 繼續訓練")
    args = parser.parse_args()
    train(args)