import gymnasium as gym
from stable_baselines3 import DQN
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common import results_plotter
import matplotlib.pyplot as plt
import numpy as np
import os
from jazz_env import JazzImprovisationEnv

# === TRAINING CONFIGURATION ===
MODEL_NAME = "jazz_model"
LOG_DIR = "training_logs/"
TIMESTEPS = 200000  # About 1500 episodes worth of training

os.makedirs(LOG_DIR, exist_ok=True)

# === SETUP ENVIRONMENT ===
# Monitor wrapper tracks episode rewards for analysis
env = JazzImprovisationEnv()
env = Monitor(env, LOG_DIR)

# Start fresh - remove any existing model
if os.path.exists(f"{MODEL_NAME}.zip"):
    os.remove(f"{MODEL_NAME}.zip")
    print("Deleted old model to start fresh.")

# === INITIALIZE MODEL ===
# DQN is good for discrete action spaces (our 38 possible actions)
model = DQN(
    "MultiInputPolicy",
    env,
    verbose=1,
    learning_rate=1e-4,  # Slow and steady learning
    buffer_size=50000,  # Remember 50k past experiences
    exploration_fraction=0.4,  # Explore for first 40% of training
    exploration_final_eps=0.05  # Always keep 5% randomness
)

# === TRAIN ===
print(f"Starting Training for {TIMESTEPS} steps...")
model.learn(total_timesteps=TIMESTEPS)
print("Training Finished!")

model.save(MODEL_NAME)
print("Model Saved.")


# === GENERATE TRAINING GRAPH ===
def plot_results(log_folder, title='JazzMate Learning Curve'):
    """
    Reads the monitor.csv and creates a learning curve visualization
    """
    try:
        # Load training data from Monitor logs
        results = results_plotter.load_results(log_folder)
        x, y = results_plotter.ts2xy(results, 'timesteps')

        if len(x) > 0:
            plt.figure(figsize=(12, 6))

            # Raw episode rewards (faded gray)
            plt.plot(x, y, alpha=0.3, color='gray', label='Episode Reward (Raw)')

            # Moving average to show the trend
            window = 100
            if len(y) > window:
                y_smoothed = np.convolve(y, np.ones(window) / window, mode='valid')
                x_smoothed = x[len(x) - len(y_smoothed):]
                plt.plot(x_smoothed, y_smoothed, linewidth=2, color='blue', label=f'Moving Average ({window} eps)')

            plt.xlabel('Timesteps (Notes Played)')
            plt.ylabel('Reward')
            plt.title(title)
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.6)

            # Save the graph
            plt.savefig("training_graph.png")
            print("\n✅ Graph saved as 'training_graph.png'")
            # plt.show()  # Uncomment if running with a display
        else:
            print("⚠️ Not enough data to plot.")

    except Exception as e:
        print(f"❌ Error plotting graph: {e}")


plot_results(LOG_DIR)