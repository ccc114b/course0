"""
BipedalWalker-v3 推論腳本
載入已訓練的 SAC 檢查點，讓智能體在環境中行走展示
"""
import argparse
import os

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn


# ─────────────────────────────────────────────────────────────
#  裝置自動偵測（CUDA → MPS → CPU）
# ─────────────────────────────────────────────────────────────
def get_device() -> torch.device:
    """自動選擇可用的計算裝置，優先順序：CUDA > MPS > CPU"""
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# ─────────────────────────────────────────────────────────────
#  最小化 Actor 網路（僅需前向推論，不含訓練邏輯）
# ─────────────────────────────────────────────────────────────
# 對數標準差的上下界，防止數值不穩定
LOG_STD_MIN, LOG_STD_MAX = -5, 2


class GaussianActor(nn.Module):
    """輸出高斯分布的 Actor，支援確定性與隨機兩種推論模式"""
    def __init__(self, obs_dim: int, act_dim: int, hidden: int, act_scale: torch.Tensor):
        super().__init__()
        # 共享隱藏層：兩層全連接 + ReLU
        self.shared = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden),  nn.ReLU(),
        )
        # 分別輸出均值與對數標準差
        self.mu_head      = nn.Linear(hidden, act_dim)
        self.log_std_head = nn.Linear(hidden, act_dim)
        # 動作縮放因子（環境的 action high），註冊為 buffer 以自動跟隨裝置移動
        self.register_buffer("act_scale", act_scale)

    def get_action(self, obs, deterministic: bool = True):
        """根據觀測產生動作，可選擇確定性（取均值）或隨機（高斯抽樣）"""
        h       = self.shared(obs)
        mu      = self.mu_head(h)
        log_std = self.log_std_head(h).clamp(LOG_STD_MIN, LOG_STD_MAX)
        if deterministic:
            # 確定性模式：直接使用 tanh(均值) 作為動作
            return torch.tanh(mu) * self.act_scale
        # 隨機模式：從高斯分布抽樣後經 tanh 壓縮
        std  = log_std.exp()
        x_t  = torch.distributions.Normal(mu, std).rsample()
        return torch.tanh(x_t) * self.act_scale


# ─────────────────────────────────────────────────────────────
#  從檢查點載入 Actor 網路權重
# ─────────────────────────────────────────────────────────────
def load_actor(ckpt_path: str, obs_dim: int, act_dim: int,
               act_scale: np.ndarray, hidden: int,
               device: torch.device) -> GaussianActor:
    """從 .pt 檔案載入 Actor 權重，設為評估模式"""
    scale_t = torch.FloatTensor(act_scale).to(device)
    actor   = GaussianActor(obs_dim, act_dim, hidden, scale_t).to(device)
    ckpt    = torch.load(ckpt_path, map_location=device)
    actor.load_state_dict(ckpt["actor"])
    actor.eval()
    print(f"[Load] {ckpt_path}")
    return actor


# ─────────────────────────────────────────────────────────────
#  執行單一回合
# ─────────────────────────────────────────────────────────────
@torch.no_grad()
def run_episode(env: gym.Env, actor: GaussianActor,
                device: torch.device, deterministic: bool = True) -> float:
    """在環境中執行一個完整回合，回傳累積報酬"""
    obs, _ = env.reset()
    total_reward = 0.0

    while True:
        # 將觀測轉為張量並增加批次維度
        obs_t  = torch.FloatTensor(obs).unsqueeze(0).to(device)
        action = actor.get_action(obs_t, deterministic=deterministic)
        action = action.squeeze(0).cpu().numpy()

        obs, reward, terminated, truncated, _ = env.step(action)
        total_reward += reward
        if terminated or truncated:
            break

    return total_reward


# ─────────────────────────────────────────────────────────────
#  主程式
# ─────────────────────────────────────────────────────────────
def main():
    """解析命令列參數，載入模型，執行指定回合數的推論"""
    parser = argparse.ArgumentParser(description="執行已訓練的 SAC BipedalWalker 智能體")
    parser.add_argument("--ckpt",        default="checkpoints/sac_best.pt",
                        help="檢查點路徑 (.pt)")
    parser.add_argument("--episodes",    type=int, default=3,
                        help="執行的回合數")
    parser.add_argument("--hidden",      type=int, default=256,
                        help="隱藏層維度（須與訓練時一致）")
    parser.add_argument("--stochastic",  action="store_true",
                        help="使用隨機（抽樣）策略而非確定性均值")
    parser.add_argument("--record",      action="store_true",
                        help="將回合錄製為 MP4（儲存在 recordings/）")
    parser.add_argument("--record-dir",  default="recordings",
                        help="錄影輸出目錄")
    parser.add_argument("--no-render",   action="store_true",
                        help="關閉渲染視窗（與 --record 搭配使用）")
    args = parser.parse_args()

    device = get_device()
    print(f"[Device] {device}")

    if not os.path.exists(args.ckpt):
        print(f"[Error] 找不到檢查點: {args.ckpt}")
        print("  → 請先執行 train.py，或使用 --ckpt 指定路徑")
        return

    # 建立環境（根據是否錄影決定渲染模式）
    if args.record:
        os.makedirs(args.record_dir, exist_ok=True)
        base_env  = gym.make("BipedalWalker-v3", render_mode="rgb_array")
        env       = gym.wrappers.RecordVideo(
            base_env,
            video_folder=args.record_dir,
            episode_trigger=lambda _: True,   # 錄製每個回合
            name_prefix="bipedal",
        )
    elif args.no_render:
        env = gym.make("BipedalWalker-v3")
    else:
        env = gym.make("BipedalWalker-v3", render_mode="human")

    obs_dim   = env.observation_space.shape[0]
    act_dim   = env.action_space.shape[0]
    act_scale = env.action_space.high

    actor = load_actor(args.ckpt, obs_dim, act_dim, act_scale, args.hidden, device)

    deterministic = not args.stochastic
    mode_str      = "deterministic" if deterministic else "stochastic"
    print(f"\n以 {mode_str} 模式執行 {args.episodes} 個回合 …\n")

    returns = []
    for ep in range(1, args.episodes + 1):
        ret = run_episode(env, actor, device, deterministic=deterministic)
        returns.append(ret)
        # BipedalWalker 的解決門檻為平均 300 分
        status = "✓ SOLVED" if ret >= 300 else ""
        print(f"  Episode {ep:>2}: return = {ret:>8.2f}  {status}")

    env.close()

    print(f"\n{'─'*40}")
    print(f"  Mean return : {np.mean(returns):>8.2f}")
    print(f"  Std  return : {np.std(returns):>8.2f}")
    print(f"  Min  return : {np.min(returns):>8.2f}")
    print(f"  Max  return : {np.max(returns):>8.2f}")
    if args.record:
        print(f"\n  Videos saved → {os.path.abspath(args.record_dir)}/")


if __name__ == "__main__":
    main()
