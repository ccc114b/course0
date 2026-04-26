"""
Breakout DQN Runner
===================
載入訓練好的模型實際遊玩 / 錄影 Breakout

依賴安裝：
    pip install torch torchvision gymnasium[atari] ale-py opencv-python

用法：
    python run.py                                      # 使用預設 best_model.pt 遊玩
    python run.py --model checkpoints/dqn_ep1000.pt   # 指定 checkpoint
    python run.py --episodes 5 --record                # 錄下 5 回合影片
    python run.py --fps 30                             # 控制播放速度
    python run.py --no-render                          # 不渲染（純跑分）
"""

import os
import time
import argparse

import numpy as np
import torch
import torch.nn as nn
import ale_py
import gymnasium as gym
from gymnasium.wrappers import AtariPreprocessing, FrameStackObservation
gym.register_envs(ale_py)   # 註冊 ALE/Breakout 等 Atari 環境

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# ─────────────────────────────────────────
#  常數（需與 train.py 一致）
# ─────────────────────────────────────────
DEVICE = torch.device(
    "cuda"  if torch.cuda.is_available() else
    "mps"   if torch.backends.mps.is_available() else
    "cpu"
)
STACK_SIZE = 4
IMG_SIZE   = 84
FRAME_SKIP = 4


# ─────────────────────────────────────────
#  DQN 網路（與 train.py 完全相同）
# ─────────────────────────────────────────
class DQN(nn.Module):
    def __init__(self, n_actions: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(STACK_SIZE, 32, kernel_size=8, stride=4),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU(),
        )
        self.fc = nn.Sequential(
            nn.Linear(64 * 7 * 7, 512),
            nn.ReLU(),
            nn.Linear(512, n_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv(x)
        x = x.flatten(start_dim=1)
        return self.fc(x)


# ─────────────────────────────────────────
#  環境建立
# ─────────────────────────────────────────
def make_env(render: bool = True) -> gym.Env:
    render_mode = "human" if render else "rgb_array"
    env = gym.make("ALE/Breakout-v5", render_mode=render_mode, frameskip=1)
    env = AtariPreprocessing(
        env,
        noop_max=30,
        frame_skip=FRAME_SKIP,
        screen_size=IMG_SIZE,
        grayscale_obs=True,
        grayscale_newaxis=False,
        scale_obs=True,
    )
    env = FrameStackObservation(env, stack_size=STACK_SIZE)
    return env


def make_record_env(output_path: str) -> gym.Env:
    """建立可錄影的環境（rgb_array + RecordVideo）"""
    env = gym.make("ALE/Breakout-v5", render_mode="rgb_array", frameskip=1)
    env = AtariPreprocessing(
        env,
        noop_max=30,
        frame_skip=FRAME_SKIP,
        screen_size=IMG_SIZE,
        grayscale_obs=True,
        grayscale_newaxis=False,
        scale_obs=True,
    )
    env = FrameStackObservation(env, stack_size=STACK_SIZE)
    env = gym.wrappers.RecordVideo(
        env,
        video_folder=output_path,
        episode_trigger=lambda _: True,   # 每回合都錄
        name_prefix="breakout",
    )
    return env


# ─────────────────────────────────────────
#  載入模型
# ─────────────────────────────────────────
def load_model(model_path: str, n_actions: int) -> DQN:
    net = DQN(n_actions).to(DEVICE)
    state_dict = torch.load(model_path, map_location=DEVICE, weights_only=False)

    # 相容 checkpoint dict（train.py 存整個 dict）或純 state_dict
    if isinstance(state_dict, dict) and "policy_net" in state_dict:
        state_dict = state_dict["policy_net"]

    net.load_state_dict(state_dict)
    net.eval()
    print(f"[Model] 已載入：{model_path}")
    return net


# ─────────────────────────────────────────
#  貪婪策略（純推論，不探索）
# ─────────────────────────────────────────
@torch.no_grad()
def greedy_action(net: DQN, obs) -> int:
    state = np.array(obs, dtype=np.float32)
    tensor = torch.from_numpy(state).unsqueeze(0).to(DEVICE)
    q = net(tensor)
    return q.argmax(dim=1).item()


# ─────────────────────────────────────────
#  執行單回合
# ─────────────────────────────────────────
def run_episode(env: gym.Env, net: DQN, fps: float, render: bool) -> float:
    obs, _ = env.reset()
    total_reward = 0.0
    step = 0
    frame_time = 1.0 / fps if fps > 0 else 0

    while True:
        t_start = time.perf_counter()

        action = greedy_action(net, obs)
        obs, reward, terminated, truncated, _ = env.step(action)
        total_reward += reward
        step += 1

        if render and frame_time > 0:
            elapsed = time.perf_counter() - t_start
            wait = frame_time - elapsed
            if wait > 0:
                time.sleep(wait)

        if terminated or truncated:
            break

    return total_reward


# ─────────────────────────────────────────
#  主程式
# ─────────────────────────────────────────
def run(args):
    print(f"[Device] {DEVICE}")

    # ── 決定 model path ──
    model_path = args.model
    if model_path is None:
        candidates = [
            os.path.join(args.checkpoint_dir, "best_model.pt"),
            os.path.join(args.checkpoint_dir,
                         sorted([f for f in os.listdir(args.checkpoint_dir)
                                 if f.endswith(".pt") and f != "best_model.pt"],
                                key=lambda f: int(f.split("_ep")[1].split(".")[0]))[-1])
            if os.path.isdir(args.checkpoint_dir) else None,
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                model_path = c
                break

    if model_path is None or not os.path.isfile(model_path):
        print(
            "[Error] 找不到模型檔案！\n"
            "  請先執行 python train.py 訓練，或用 --model <path> 指定模型路徑。"
        )
        return

    # ── 建立環境 ──
    do_render = not args.no_render
    if args.record:
        os.makedirs("recordings", exist_ok=True)
        env = make_record_env("recordings")
        print("[Record] 影片將存至 recordings/")
    else:
        env = make_env(render=do_render)

    n_actions = env.action_space.n
    net = load_model(model_path, n_actions)

    print(f"\n開始遊玩 {args.episodes} 回合 ...")
    print(f"  FPS 限制：{args.fps if args.fps > 0 else '無限制'}")
    print(f"  動作數：{n_actions}\n")

    all_rewards = []

    for ep in range(1, args.episodes + 1):
        reward = run_episode(env, net, fps=args.fps, render=do_render)
        all_rewards.append(reward)
        print(f"  回合 {ep:3d}：獎勵 = {reward:.1f}")

    env.close()

    # ── 統計 ──
    print("\n" + "=" * 40)
    print(f"  回合數   ：{args.episodes}")
    print(f"  平均獎勵 ：{np.mean(all_rewards):.2f}")
    print(f"  最高獎勵 ：{np.max(all_rewards):.1f}")
    print(f"  最低獎勵 ：{np.min(all_rewards):.1f}")
    print("=" * 40)

    if args.record:
        print("\n影片已儲存至 recordings/ 資料夾。")


# ─────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run trained DQN on Breakout")
    parser.add_argument("--model",           type=str,  default=None,
                        help="模型 .pt 路徑（預設自動找 checkpoints/best_model.pt）")
    parser.add_argument("--checkpoint-dir",  type=str,  default="checkpoints",
                        help="checkpoint 資料夾（auto-find 用）")
    parser.add_argument("--episodes",        type=int,  default=3,
                        help="遊玩回合數 (default: 3)")
    parser.add_argument("--fps",             type=float, default=30.0,
                        help="畫面更新速度，0 = 不限制 (default: 30)")
    parser.add_argument("--record",          action="store_true",
                        help="錄下影片到 recordings/ 資料夾")
    parser.add_argument("--no-render",       action="store_true",
                        help="不開視窗（只計算分數）")
    args = parser.parse_args()
    run(args)