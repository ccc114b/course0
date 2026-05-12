# 載入已訓練的 PPO 模型，在 Walker2d-v5 環境中展示行走效果
import gymnasium as gym
import torch
import numpy as np
import time
from model import ActorCritic

def run():
    env = gym.make("Walker2d-v5", render_mode="human")
    
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    model = ActorCritic(state_dim, action_dim)
    
    # 載入檢查點：包含模型權重與歸一化統計參數
    checkpoint = torch.load("ppo_walker_diy.pth", weights_only=False)
    model.load_state_dict(checkpoint['model'])
    rms_mean = checkpoint['rms_mean']
    rms_var = checkpoint['rms_var']
    model.eval()

    state, _ = env.reset()
    
    while True:
        # 使用訓練時累積的統計資料進行狀態歸一化
        norm_s = (state - rms_mean) / np.sqrt(rms_var + 1e-8)
        s_ts = torch.FloatTensor(norm_s).unsqueeze(0)
        
        with torch.no_grad():
            action = model.actor(s_ts)
            
        state, reward, term, trunc, _ = env.step(action.cpu().numpy().flatten())
        
        # 更新攝影機以跟隨 Walker 的 x 軸位置（torso 座標）
        if hasattr(env.unwrapped, 'mujoco_renderer') and env.unwrapped.mujoco_renderer is not None:
            walker_x = env.unwrapped.data.qpos[0]
            env.unwrapped.mujoco_renderer.viewer.cam.lookat[0] = walker_x
            env.unwrapped.mujoco_renderer.viewer.cam.lookat[1] = 0.0
            env.unwrapped.mujoco_renderer.viewer.cam.lookat[2] = 1.0
        
        env.render()
        time.sleep(0.01)
        
        if term or trunc:
            state, _ = env.reset()

if __name__ == "__main__":
    run()