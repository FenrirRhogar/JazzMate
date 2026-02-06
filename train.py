import gymnasium as gym
from stable_baselines3 import DQN
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common import results_plotter
import matplotlib.pyplot as plt
import numpy as np
import os
from jazz_env import JazzImprovisationEnv

# --- ΡΥΘΜΙΣΕΙΣ ΕΚΠΑΙΔΕΥΣΗΣ ---
MODEL_NAME = "jazz_dqn_model"
LOG_DIR = "training_logs/"
TIMESTEPS = 200000

# Δημιουργία φακέλου για τα logs
os.makedirs(LOG_DIR, exist_ok=True)

# 1. Δημιουργία Περιβάλλοντος με Monitor (Καταγράφει τα rewards)
env = JazzImprovisationEnv()
env = Monitor(env, LOG_DIR)

# Διαγραφή παλιού μοντέλου για καθαρή αρχή
if os.path.exists(f"{MODEL_NAME}.zip"):
    os.remove(f"{MODEL_NAME}.zip")
    print("Deleted old model to start fresh.")

# 2. Ορισμός Μοντέλου
model = DQN(
    "MultiInputPolicy",
    env,
    verbose=1,
    learning_rate=1e-4,
    buffer_size=50000,
    exploration_fraction=0.4,
    exploration_final_eps=0.05
)

# 3. Εκπαίδευση
print(f"Starting Training for {TIMESTEPS} steps...")
model.learn(total_timesteps=TIMESTEPS)
print("Training Finished!")

# Αποθήκευση
model.save(MODEL_NAME)
print("Model Saved.")


# 4. Αυτόματη Δημιουργία Γραφήματος
def plot_results(log_folder, title='JazzMate Learning Curve'):
    """
    Διαβάζει το monitor.csv και δημιουργεί γράφημα
    """
    try:
        # Φόρτωση δεδομένων από το Monitor
        results = results_plotter.load_results(log_folder)
        x, y = results_plotter.ts2xy(results, 'timesteps')

        if len(x) > 0:
            plt.figure(figsize=(12, 6))

            # Raw Data (Αχνό γκρι)
            plt.plot(x, y, alpha=0.3, color='gray', label='Episode Reward (Raw)')

            # Moving Average (Μπλε γραμμή - Τάση)
            window = 100
            if len(y) > window:
                y_smoothed = np.convolve(y, np.ones(window) / window, mode='valid')
                x_smoothed = x[len(x) - len(y_smoothed):]
                plt.plot(x_smoothed, y_smoothed, linewidth=2, color='blue', label=f'Moving Average ({window} eps)')

            plt.xlabel('Timesteps (Νότες που έπαιξε)')
            plt.ylabel('Reward (Επιβράβευση)')
            plt.title(title)
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.6)

            # Αποθήκευση εικόνας
            plt.savefig("training_graph.png")
            print("\n✅ Graph saved as 'training_graph.png'")
            # plt.show() # Προαιρετικό, αν τρέχεις σε περιβάλλον με οθόνη
        else:
            print("⚠️ Not enough data to plot.")

    except Exception as e:
        print(f"❌ Error plotting graph: {e}")


# Κλήση της συνάρτησης
plot_results(LOG_DIR)