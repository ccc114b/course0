"""
BipedalWalker-v3 訓練腳本
演算法：SAC (Soft Actor-Critic)
框架：PyTorch + Gymnasium
"""

import os
import random
from dataclasses import dataclass

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


# ─────────────────────────────────────────────────────────────
#  超參數設定
# ─────────────────────────────────────────────────────────────
@dataclass
class Config:
    env_id: str = "BipedalWalker-v3"
    seed: int = 42

    # SAC 相關參數
    gamma: float = 0.99          # 折扣因子
    tau: float   = 0.005         # 目標網路軟更新速率
    tune_alpha: bool = True      # 是否自動調整熵溫度 α

    # 網路架構
    hidden_dim: int = 256

    # 訓練參數
    total_steps: int    = 100000  # 總訓練步數
    batch_size: int     = 256     # 每次更新的批次大小
    buffer_size: int    = 1_000_000  # 經驗回放緩衝區容量
    learning_starts: int = 10_000    # 開始學習前的最小樣本數
    lr: float           = 3e-4       # 學習率
    updates_per_step: int = 1        # 每步的更新次數

    # 紀錄與儲存
    log_interval: int  = 5_000
    save_interval: int = 50_000
    save_dir: str      = "checkpoints"


# ─────────────────────────────────────────────────────────────
#  裝置自動偵測（CUDA → MPS → CPU）
# ─────────────────────────────────────────────────────────────
def get_device() -> torch.device:
    """依可用性自動選擇計算裝置"""
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    print(f"[Device] {device}")
    return device


# ─────────────────────────────────────────────────────────────
#  經驗回放緩衝區（numpy 儲存在 CPU，取樣時搬到裝置）
# ─────────────────────────────────────────────────────────────
class ReplayBuffer:
    """環形緩衝區，儲存 (s, a, r, s', done) 轉移"""
    def __init__(self, capacity: int, obs_dim: int, act_dim: int, device: torch.device):
        self.capacity = capacity
        self.device   = device
        self.ptr      = 0       # 當前寫入位置
        self.size     = 0       # 已儲存數量

        # 預先分配 numpy 陣列
        self.obs      = np.zeros((capacity, obs_dim), dtype=np.float32)
        self.actions  = np.zeros((capacity, act_dim), dtype=np.float32)
        self.rewards  = np.zeros((capacity, 1),       dtype=np.float32)
        self.next_obs = np.zeros((capacity, obs_dim), dtype=np.float32)
        self.dones    = np.zeros((capacity, 1),       dtype=np.float32)

    def add(self, obs, action, reward, next_obs, done: float):
        """新增一筆轉移到緩衝區，指標循環移動"""
        self.obs[self.ptr]      = obs
        self.actions[self.ptr]  = action
        self.rewards[self.ptr]  = reward
        self.next_obs[self.ptr] = next_obs
        self.dones[self.ptr]    = done
        self.ptr  = (self.ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size: int):
        """隨機抽樣一個批次的轉移，回傳搬到指定裝置的張量"""
        idx = np.random.randint(0, self.size, size=batch_size)
        to  = lambda arr: torch.from_numpy(arr[idx]).to(self.device)
        return to(self.obs), to(self.actions), to(self.rewards), \
               to(self.next_obs), to(self.dones)

    def __len__(self):
        return self.size


# ─────────────────────────────────────────────────────────────
#  神經網路定義
# ─────────────────────────────────────────────────────────────
def _mlp(in_dim: int, out_dim: int, hidden: int) -> nn.Sequential:
    """建立兩層隱藏層的 MLP"""
    return nn.Sequential(
        nn.Linear(in_dim, hidden), nn.ReLU(),
        nn.Linear(hidden, hidden), nn.ReLU(),
        nn.Linear(hidden, out_dim),
    )


class TwinCritic(nn.Module):
    """雙 Q 網路：兩個獨立的 Q 估計器，減輕 Q 值高估偏差"""
    def __init__(self, obs_dim: int, act_dim: int, hidden: int):
        super().__init__()
        # 串接觀測與動作作為輸入
        self.q1 = _mlp(obs_dim + act_dim, 1, hidden)
        self.q2 = _mlp(obs_dim + act_dim, 1, hidden)

    def forward(self, obs, action):
        x = torch.cat([obs, action], dim=-1)
        return self.q1(x), self.q2(x)


# 對數標準差的限制範圍
LOG_STD_MIN, LOG_STD_MAX = -5, 2


class GaussianActor(nn.Module):
    """經 tanh 壓縮的高斯策略，使用重參數化技巧"""
    def __init__(self, obs_dim: int, act_dim: int, hidden: int, act_scale: torch.Tensor):
        super().__init__()
        # 共享特徵提取層
        self.shared       = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden),  nn.ReLU(),
        )
        # 分別輸出均值與對數標準差
        self.mu_head      = nn.Linear(hidden, act_dim)
        self.log_std_head = nn.Linear(hidden, act_dim)
        # 動作縮放因子，註冊為 buffer 以隨 .to(device) 自動移動
        self.register_buffer("act_scale", act_scale)

    def forward(self, obs):
        """前向傳播，回傳均值與對數標準差"""
        h       = self.shared(obs)
        mu      = self.mu_head(h)
        log_std = self.log_std_head(h).clamp(LOG_STD_MIN, LOG_STD_MAX)
        return mu, log_std

    def get_action(self, obs):
        """產生動作、對數機率與確定性動作（供 SAC 更新使用）"""
        mu, log_std = self.forward(obs)
        std  = log_std.exp()
        dist = torch.distributions.Normal(mu, std)
        # 重參數化抽樣，允許梯度流經抽樣過程
        x_t  = dist.rsample()
        y_t  = torch.tanh(x_t)
        action = y_t * self.act_scale

        # 考慮 tanh 壓縮的對數機率校正項
        # log π(a|s) = log π(u|s) - Σ log(scale * (1 - tanh²(u)) + ε)
        log_prob = (dist.log_prob(x_t)
                    - torch.log(self.act_scale * (1 - y_t.pow(2)) + 1e-6)
                   ).sum(dim=-1, keepdim=True)

        # 確定性動作（取均值經 tanh），用於評估時的動作選擇
        mean_action = torch.tanh(mu) * self.act_scale
        return action, log_prob, mean_action


# ─────────────────────────────────────────────────────────────
#  SAC 智能體
# ─────────────────────────────────────────────────────────────
class SAC:
    """Soft Actor-Critic 智能體，包含 Actor、雙 Critic 與可選的自動熵調整"""
    def __init__(self, obs_dim: int, act_dim: int,
                 act_scale: np.ndarray, cfg: Config, device: torch.device):
        self.cfg    = cfg
        self.device = device

        scale_t = torch.FloatTensor(act_scale).to(device)

        # 建立三個網路：Actor、Critic、目標 Critic
        self.actor         = GaussianActor(obs_dim, act_dim, cfg.hidden_dim, scale_t).to(device)
        self.critic        = TwinCritic(obs_dim, act_dim, cfg.hidden_dim).to(device)
        self.critic_target = TwinCritic(obs_dim, act_dim, cfg.hidden_dim).to(device)
        self.critic_target.load_state_dict(self.critic.state_dict())
        # 凍結目標網路參數（僅透過軟更新改變）
        for p in self.critic_target.parameters():
            p.requires_grad = False

        self.actor_opt  = optim.Adam(self.actor.parameters(),  lr=cfg.lr)
        self.critic_opt = optim.Adam(self.critic.parameters(), lr=cfg.lr)

        # 熵溫度 α：可自動調整或固定為 0.2
        self.target_entropy = float(-act_dim)          # 啟發式目標熵
        if cfg.tune_alpha:
            self.log_alpha = torch.zeros(1, requires_grad=True, device=device)
            self.alpha     = self.log_alpha.exp().item()
            self.alpha_opt = optim.Adam([self.log_alpha], lr=cfg.lr)
        else:
            self.log_alpha = None
            self.alpha     = 0.2

    # ── 軟更新目標網路 ───────────────────────
    @torch.no_grad()
    def _soft_update(self):
        """Polyak 平均：θ_target ← (1-τ)θ_target + τ θ"""
        for p, tp in zip(self.critic.parameters(),
                         self.critic_target.parameters()):
            tp.data.mul_(1 - self.cfg.tau).add_(p.data * self.cfg.tau)

    # ── 動作選擇（用於環境互動）────────────
    @torch.no_grad()
    def select_action(self, obs: np.ndarray, deterministic: bool = False) -> np.ndarray:
        """將 numpy 觀測轉為張量，回傳 numpy 動作"""
        obs_t = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        if deterministic:
            _, _, action = self.actor.get_action(obs_t)
        else:
            action, _, _ = self.actor.get_action(obs_t)
        return action.squeeze(0).cpu().numpy()

    # ── 單步梯度更新 ─────────────────────────
    def update(self, buffer: ReplayBuffer) -> dict:
        """從回放緩衝區抽樣一個批次，依序更新 Critic、Actor、α"""
        obs, actions, rewards, next_obs, dones = buffer.sample(self.cfg.batch_size)

        # ── 更新 Critic ──
        with torch.no_grad():
            # 使用目標網路計算下個狀態-動作的 Q 值
            next_a, next_log_pi, _ = self.actor.get_action(next_obs)
            q1_next, q2_next = self.critic_target(next_obs, next_a)
            # 取兩者最小值並加入熵獎勵：Q_target = min(Q1,Q2) - α logπ
            q_next    = torch.min(q1_next, q2_next) - self.alpha * next_log_pi
            q_target  = rewards + self.cfg.gamma * (1 - dones) * q_next

        q1, q2      = self.critic(obs, actions)
        # 同時最小化兩個 Q 網路的 MSE 損失
        critic_loss = F.mse_loss(q1, q_target) + F.mse_loss(q2, q_target)
        self.critic_opt.zero_grad()
        critic_loss.backward()
        self.critic_opt.step()

        # ── 更新 Actor ──
        new_a, log_pi, _ = self.actor.get_action(obs)
        q1_pi, q2_pi     = self.critic(obs, new_a)
        # Actor 目標：最大化 Q - α logπ（即最小化 α logπ - Q）
        actor_loss        = (self.alpha * log_pi - torch.min(q1_pi, q2_pi)).mean()
        self.actor_opt.zero_grad()
        actor_loss.backward()
        self.actor_opt.step()

        # ── 更新 α（若啟用自動調整）─────────
        alpha_loss_val = 0.0
        if self.cfg.tune_alpha:
            # 當 π 的熵高於目標熵時降低 α，反之提高
            alpha_loss = (-self.log_alpha.exp() *
                          (log_pi.detach() + self.target_entropy)).mean()
            self.alpha_opt.zero_grad()
            alpha_loss.backward()
            self.alpha_opt.step()
            self.alpha     = self.log_alpha.exp().item()
            alpha_loss_val = alpha_loss.item()

        self._soft_update()

        return dict(
            critic_loss = critic_loss.item(),
            actor_loss  = actor_loss.item(),
            alpha       = self.alpha,
            alpha_loss  = alpha_loss_val,
        )

    # ── 檢查點儲存與載入 ────────────────────
    def save(self, path: str):
        torch.save(dict(
            actor      = self.actor.state_dict(),
            critic     = self.critic.state_dict(),
            alpha      = self.alpha,
            log_alpha  = self.log_alpha.detach().cpu() if self.log_alpha is not None else None,
        ), path)
        print(f"[Save] {path}")

    def load(self, path: str):
        ckpt = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(ckpt["actor"])
        self.critic.load_state_dict(ckpt["critic"])
        self.critic_target.load_state_dict(ckpt["critic"])
        self.alpha = ckpt["alpha"]
        if self.log_alpha is not None and ckpt["log_alpha"] is not None:
            self.log_alpha.data.copy_(ckpt["log_alpha"].to(self.device))
        print(f"[Load] {path}")


# ─────────────────────────────────────────────────────────────
#  主訓練循環
# ─────────────────────────────────────────────────────────────
def train():
    """建立環境與 SAC 智能體，執行 main training loop"""
    cfg    = Config()
    device = get_device()

    # 設定亂數種子以確保可重現
    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)

    env     = gym.make(cfg.env_id)
    env.action_space.seed(cfg.seed)
    obs_dim   = env.observation_space.shape[0]   # 24 維觀測
    act_dim   = env.action_space.shape[0]         # 4 維連續動作
    act_scale = env.action_space.high             # [1, 1, 1, 1]

    agent  = SAC(obs_dim, act_dim, act_scale, cfg, device)
    buffer = ReplayBuffer(cfg.buffer_size, obs_dim, act_dim, device)

    os.makedirs(cfg.save_dir, exist_ok=True)

    obs, _       = env.reset(seed=cfg.seed)
    ep_ret       = 0.0
    ep_len       = 0
    ep_count     = 0
    recent_rets: list[float] = []
    best_mean    = -float("inf")

    print(f"\n{'═'*60}")
    print(f"  BipedalWalker-v3  ·  SAC  ·  {device}")
    print(f"  obs={obs_dim}  act={act_dim}  steps={cfg.total_steps:,}")
    print(f"{'═'*60}\n")

    for step in range(1, cfg.total_steps + 1):

        # 收集資料：學習開始前使用隨機動作探索
        if step < cfg.learning_starts:
            action = env.action_space.sample()
        else:
            action = agent.select_action(obs)

        next_obs, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated

        # 儲存轉移（使用 terminated 而非 truncated，避免 bootstrap 誤差）
        buffer.add(obs, action, reward, next_obs, float(terminated))
        obs    = next_obs
        ep_ret += reward
        ep_len += 1

        if done:
            recent_rets.append(ep_ret)
            if len(recent_rets) > 20:
                recent_rets.pop(0)
            ep_count += 1
            obs, _ = env.reset()
            ep_ret = ep_len = 0

        # 更新網路：需有足夠樣本才開始學習
        if step >= cfg.learning_starts and len(buffer) >= cfg.batch_size:
            for _ in range(cfg.updates_per_step):
                agent.update(buffer)

        # 記錄訓練統計
        if step % cfg.log_interval == 0:
            mean_ret = np.mean(recent_rets) if recent_rets else float("nan")
            print(f"step {step:>8,} | ep {ep_count:>5} | "
                  f"return(avg20) {mean_ret:>8.2f} | "
                  f"α {agent.alpha:.4f} | buf {len(buffer):,}")

        # 定期儲存檢查點
        if step % cfg.save_interval == 0:
            agent.save(os.path.join(cfg.save_dir, f"sac_step{step}.pt"))
            mean_ret = np.mean(recent_rets) if recent_rets else -9999
            if mean_ret > best_mean:
                best_mean = mean_ret
                agent.save(os.path.join(cfg.save_dir, "sac_best.pt"))
                print(f"  ★ New best mean return: {best_mean:.2f}")

    env.close()
    agent.save(os.path.join(cfg.save_dir, "sac_final.pt"))
    print("\n[Done] Training finished.")


if __name__ == "__main__":
    train()
