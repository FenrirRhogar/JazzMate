import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random

# Map chord names to their constituent notes (in chromatic scale 0-11)
CHORD_MAPPING = {
    "Cm7": [0, 3, 7, 10], "F7": [5, 9, 0, 3],
    "BbMaj7": [10, 2, 5, 9], "EbMaj7": [3, 7, 10, 2],
    "Am7b5": [9, 0, 3, 7], "D7": [2, 6, 9, 0],
    "Gm": [7, 10, 2, 5], "Dm7": [2, 5, 9, 0],
    "G7": [7, 11, 2, 5], "CMaj7": [0, 4, 7, 11],
    "C7b9": [0, 4, 7, 10, 1], "Fdim7": [5, 8, 11, 2],
    "Bb6": [10, 2, 5, 7], "E7alt": [4, 8, 0, 2]
}


class JazzImprovisationEnv(gym.Env):
    metadata = {'render_modes': ['console']}

    def __init__(self):
        super(JazzImprovisationEnv, self).__init__()
        # Actions: 0-35 are notes (3 octaves), 36 is rest, 37 is hold
        self.action_space = spaces.Discrete(38)

        self.observation_space = spaces.Dict({
            "chord_tones": spaces.Box(low=0, high=1, shape=(12,), dtype=np.int8),
            "step_progress": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
            "last_action": spaces.Discrete(38),
            "held_duration": spaces.Box(low=0, high=128, shape=(1,), dtype=np.float32),
            "style_seed": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
        })

        self.progression = []
        self.steps_per_episode = 0
        self.current_step = 0
        self.current_chord_name = "Cm7"
        self.last_action = 36
        self.current_action_duration = 0
        self.history = [36] * 16
        self.current_style = 0.5

        # Track note patterns to prevent spam and encourage variety
        self.consecutive_notes = 0
        self.exact_note_repeats = 0
        self.last_note_played = 36
        self.consecutive_varied_notes = 0

        self.manual_mode = False

    def set_manual_chord(self, chord_name):
        if chord_name in CHORD_MAPPING:
            self.current_chord_name = chord_name
            self.manual_mode = True

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Generate a random chord progression (8 chords, each lasting 16 steps)
        available_chords = list(CHORD_MAPPING.keys())
        self.progression = []
        for _ in range(8):
            chord = random.choice(available_chords)
            self.progression.extend([chord] * 16)
        self.steps_per_episode = len(self.progression)

        self.current_step = 0
        self.last_action = 36
        self.consecutive_notes = 0
        self.exact_note_repeats = 0
        self.last_note_played = 36
        self.consecutive_varied_notes = 0
        self.current_action_duration = 0
        self.history = [36] * 16
        self.current_chord_name = self.progression[0]
        self.current_style = random.random()
        self.manual_mode = False
        return self._get_obs(), {}

    def _get_obs(self):
        if not self.manual_mode:
            if self.current_step < len(self.progression):
                prev_chord = self.current_chord_name
                self.current_chord_name = self.progression[self.current_step]
                # Change style seed when we hit a new chord to encourage variation
                if self.current_chord_name != prev_chord:
                    self.current_style = random.random()

        chord_vector = np.zeros(12, dtype=np.int8)
        current_notes = CHORD_MAPPING[self.current_chord_name]
        for note in current_notes:
            chord_vector[note % 12] = 1

        progress = np.array([self.current_step / self.steps_per_episode], dtype=np.float32)
        duration = np.array([self.current_action_duration], dtype=np.float32)
        style = np.array([self.current_style], dtype=np.float32)

        return {
            "chord_tones": chord_vector, "step_progress": progress,
            "last_action": self.last_action, "held_duration": duration, "style_seed": style
        }

    def step(self, action):
        # Track how long the current action has been held
        is_hold = (action == 37)
        if is_hold:
            self.current_action_duration += 1
        elif action == self.last_action and action == 36:
            self.current_action_duration += 1
        else:
            self.current_action_duration = 1

        # Calculate reward based on the CURRENT state, before updates
        reward = self._calculate_reward(action)

        # Update counters for the next state
        if action < 36:  # Note played
            self.consecutive_notes += 1
            if action == self.last_note_played:
                self.exact_note_repeats += 1
                self.consecutive_varied_notes = 1  # Reset variety on repeat
            else:
                self.exact_note_repeats = 0
                self.consecutive_varied_notes += 1  # Increment on variety
            self.last_note_played = action
        else:  # Rest or Hold
            self.consecutive_notes = 0
            self.exact_note_repeats = 0
            self.consecutive_varied_notes = 0  # Reset variety on break

        self.history.append(action)
        if len(self.history) > 16: self.history.pop(0)

        self.last_action = action
        self.current_step += 1
        terminated = self.current_step >= self.steps_per_episode
        return self._get_obs(), reward, terminated, False, {"chord": self.current_chord_name}

    def _calculate_reward(self, action):
        reward = 0.0
        chord_notes = CHORD_MAPPING[self.current_chord_name]
        chord_notes_set = set(n % 12 for n in chord_notes)
        is_note = action < 36
        is_rest = action == 36
        is_hold = action == 37
        prev1 = self.history[-2]

        # === HARMONY ===
        # Playing chord tones sounds good, non-chord tones sound bad
        if is_note:
            if (action % 12) in chord_notes_set:
                reward += 1.0
            else:
                reward -= 0.6

        # === MELODIC FLOW ===
        # Stepwise motion sounds smooth, big jumps sound awkward
        if is_note and prev1 < 36:
            interval = abs(action - prev1)
            if 1 <= interval <= 2:
                reward += 0.8
            elif 3 <= interval <= 5:
                reward += 0.4
            elif interval > 9:
                reward -= 1.5

        # === ANTI-SPAM ===
        # Repeating the exact same note over and over is boring
        if is_note:
            if self.exact_note_repeats == 1:
                reward -= 2.0
            elif self.exact_note_repeats >= 2:
                reward -= 10.0  # Really don't do this

        # === PHRASE LOOPS ===
        # Short repeating patterns get old fast
        if len(self.history) >= 4 and self.history[-2:] == self.history[-4:-2]:
            reward -= 5.0
        if len(self.history) >= 6 and self.history[-3:] == self.history[-6:-3]:
            reward -= 10.0
        if len(self.history) >= 8 and self.history[-4:] == self.history[-8:-4]:
            reward -= 15.0

        # === FATIGUE ===
        # Playing too many notes in a row without a break gets tiring
        if is_note:
            if self.consecutive_notes > 8:
                reward -= (self.consecutive_notes * 0.4)

        # === DYNAMIC HOLD ===
        # Holding a note can add expression, but not forever
        if is_hold:
            last_played = next((a for a in reversed(self.history[:-1]) if a < 36), -1)
            if last_played != -1 and (last_played % 12) in chord_notes_set:
                if self.current_action_duration <= 4:
                    reward += 1.2
                elif self.current_action_duration <= 8:
                    reward += 0.5
                else:
                    reward -= 1.0
            else:
                reward -= 1.0

        # === REST ===
        # Resting at the right time creates good phrasing
        if is_rest:
            # Big reward for resting after a good riff (phrasing)
            if self.consecutive_varied_notes >= 4:
                reward += 3.0
            # Existing logic for general phrasing
            elif self.consecutive_notes >= 4:
                reward += 2.0
            elif self.consecutive_notes == 1:
                reward -= 0.8
            elif self.current_action_duration > 6:
                reward -= 1.0
            else:
                reward -= 0.1

        # === RIFF BONUS ===
        # Playing varied notes in a sequence creates interesting phrases
        if self.consecutive_varied_notes == 4:
            reward += 2.5
        elif self.consecutive_varied_notes >= 5:
            reward += 4.0

        return reward