# https://github.com/weixiang0470/ai112b/blob/master/Homework/hw08/cartpole1.py

import gymnasium as gym
# 使用 human 模式渲染畫面
env = gym.make("CartPole-v1", render_mode="human")
observation, info = env.reset(seed=42)
steps = 0
for _ in range(2000):
   env.render()

   # 閉合形式控制法則：根據杆子角度 θ (observation[2]) 與角速度 θ' (observation[3]) 決策
   # 當杆子向右傾 (θ > 0) 且角速度大於 0.01 時，連續向右推兩次以快速矯正
   if observation[2] > 0 : 
    if observation[3] > 0.01 :
        action = 1 
        observation, reward, terminated, truncated, info = env.step(action)
        steps += 1
        observation, reward, terminated, truncated, info = env.step(action)
        steps += 1
    else : 
       action = 0
       observation, reward, terminated, truncated, info = env.step(action)
       steps += 1
   # 當杆子向左傾 (θ < 0) 且角速度小於 -0.01 時，連續向左推兩次
   elif observation[2] < 0 : 
    if observation[3] < -0.01 :
        action = 0 
        observation, reward, terminated, truncated, info = env.step(action)
        steps += 1
        observation, reward, terminated, truncated, info = env.step(action)
        steps += 1
    else : 
       action = 1
       observation, reward, terminated, truncated, info = env.step(action)
       steps += 1
   
   if terminated or truncated:
      observation, info = env.reset()
      print('steps:',steps)
      steps = 0

env.close()