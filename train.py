import gymnasium as gym
from stable_baselines3 import DQN
from jazz_env import JazzImprovisationEnv
import os

env = JazzImprovisationEnv()

if os.path.exists("jazz_dqn_model.zip"):
    os.remove("jazz_dqn_model.zip")
    print("Deleted old model to start fresh.")

model = DQN(
    "MultiInputPolicy",
    env,
    verbose=1,
    learning_rate=1e-4,
    buffer_size=50000,
    exploration_fraction=0.4,
    exploration_final_eps=0.05
)

TIMESTEPS = 200000

print(f"Starting Training for {TIMESTEPS} steps...")
model.learn(total_timesteps=TIMESTEPS)

print("Training Finished!")
model.save("jazz_dqn_model")