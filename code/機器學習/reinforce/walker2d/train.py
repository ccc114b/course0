# PPO (Proximal Policy Optimization) 訓練腳本 — Walker2d-v5
import gymnasium as gym
import torch
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
from model import ActorCritic, RunningMeanStd

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

# 實測 CPU 反而更快（資料量不夠大時 GPU 開銷 > 收益）
device = torch.device("cpu")
print(f"使用 device: {device}")

def train():
    env = gym.make("Walker2d-v5")
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    
    policy = ActorCritic(state_dim, action_dim).to(device)
    optimizer = optim.Adam(policy.parameters(), lr=3e-4)
    # 狀態歸一化器：在資料收集過程中線上更新均值與變異數
    rms = RunningMeanStd(state_dim)
    
    print("開始訓練 (優化版)...")

    for i_update in range(1000):
        buffer_s, buffer_a, buffer_lp, buffer_r, buffer_d = [], [], [], [], []
        state, _ = env.reset()
        
        # ── 1. 收集數據 ──────────────────────
        for t in range(2048):
            rms.update(state.reshape(1, -1))
            # 歸一化：將狀態減均值除標準差
            norm_s = (state - rms.mean) / np.sqrt(rms.var + 1e-8)
            
            s_ts = torch.FloatTensor(norm_s).unsqueeze(0).to(device)
            action, logprob = policy.get_action(s_ts)
            
            next_state, reward, term, trunc, _ = env.step(action.cpu().numpy().flatten())
            
            # 獎勵縮放：MuJoCo 獎勵範圍較大，除以 10 以穩定訓練
            buffer_s.append(s_ts)
            buffer_a.append(action)
            buffer_lp.append(logprob)
            buffer_r.append(reward / 10.0) 
            buffer_d.append(term or trunc)
            
            state = next_state
            if term or trunc: state, _ = env.reset()

        # ── 2. 計算 Returns 與 Advantages ────
        s_batch = torch.cat(buffer_s)
        a_batch = torch.cat(buffer_a)
        lp_batch = torch.cat(buffer_lp).detach()
        
        with torch.no_grad():
            _, v_batch, _ = policy.evaluate(s_batch, a_batch)
            v_batch = v_batch.squeeze()
            
            # 從後往前計算折扣回報
            ret = 0
            returns = []
            for r, d in zip(reversed(buffer_r), reversed(buffer_d)):
                if d: ret = 0
                ret = r + 0.99 * ret
                returns.insert(0, ret)
            
            returns = torch.FloatTensor(returns).to(device)
            # 優勢函數：Returns - V(s)
            advantages = (returns - v_batch)
            # 優勢歸一化：減均值除標準差，穩定訓練
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # ── 3. PPO 更新（多輪）───────────────
        for _ in range(10):
            new_lp, v_s, entropy = policy.evaluate(s_batch, a_batch)
            # 新舊策略比率
            ratio = torch.exp(new_lp - lp_batch)
            # 裁剪目標：限制比率在 [0.8, 1.2] 之間
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 0.8, 1.2) * advantages
            
            # 總損失 = PPO 裁剪目標 + 價值損失 + 熵獎勵
            loss = -torch.min(surr1, surr2) + 0.5 * F.mse_loss(v_s.squeeze(), returns) - 0.01 * entropy
            optimizer.zero_grad()
            loss.mean().backward()
            optimizer.step()

        # 每 20 次更新輸出訓練統計並儲存檢查點
        if i_update % 20 == 0:
            print(f"Update {i_update} | Mean Reward: {np.mean(buffer_r)*10:.2f}")
            torch.save({
                'model': policy.state_dict(),
                'rms_mean': rms.mean,
                'rms_var': rms.var
            }, "ppo_walker_diy.pth")

if __name__ == "__main__":
    train()