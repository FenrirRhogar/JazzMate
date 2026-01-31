import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random

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

        # ΝΕΟΙ ΜΕΤΡΗΤΕΣ
        self.consecutive_notes = 0  # Γενική κούραση (οποιαδήποτε νότα)
        self.exact_note_repeats = 0  # Κούραση ΙΔΙΑΣ νότας (Spamming)

        self.manual_mode = False

    def set_manual_chord(self, chord_name):
        if chord_name in CHORD_MAPPING:
            self.current_chord_name = chord_name
            self.manual_mode = True

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        available_chords = list(CHORD_MAPPING.keys())
        self.progression = []
        for _ in range(8):
            chord = random.choice(available_chords)
            self.progression.extend([chord] * 16)
        self.steps_per_episode = len(self.progression)

        self.current_step = 0
        self.last_action = 36
        self.consecutive_notes = 0
        self.exact_note_repeats = 0  # Reset
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
        is_hold = (action == 37)
        if is_hold:
            self.current_action_duration += 1
        elif action == self.last_action and action == 36:
            self.current_action_duration += 1
        else:
            self.current_action_duration = 1

        # Ενημέρωση μετρητών ΠΡΙΝ το reward
        if action < 36:  # Note played
            self.consecutive_notes += 1
            if action == self.last_action:
                self.exact_note_repeats += 1
            else:
                self.exact_note_repeats = 0
        elif action == 36:  # Rest
            self.consecutive_notes = 0
            self.exact_note_repeats = 0
        # Hold doesn't reset exact_repeats, but doesn't increase them either

        self.history.append(action)
        if len(self.history) > 16: self.history.pop(0)

        reward = self._calculate_reward(action)

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

        # 1. HARMONY
        if is_note:
            if (action % 12) in chord_notes_set:
                reward += 1.0
            else:
                reward -= 0.6

            # 2. MELODIC FLOW
        if is_note and prev1 < 36:
            interval = abs(action - prev1)
            if 1 <= interval <= 2:
                reward += 0.8
            elif 3 <= interval <= 5:
                reward += 0.4
            elif interval > 9:
                reward -= 0.3

        # 3. ANTI-SPAM (NUCLEAR OPTION)
        if is_note:
            if self.exact_note_repeats == 1:
                reward -= 2.0  # Μην το ξαναπαίξεις
            elif self.exact_note_repeats >= 2:
                reward -= 10.0  # ΑΠΑΓΟΡΕΥΕΤΑΙ - Θα μάθει να μην το κάνει ποτέ

        # 4. PHRASE LOOPS
        last_3 = self.history[-3:]
        prev_3 = self.history[-6:-3]
        if last_3 == prev_3: reward -= 5.0  # Αυστηρότερο loop check

        # 5. FATIGUE
        if is_note:
            if self.consecutive_notes > 6: reward -= (self.consecutive_notes * 0.5)

        # 6. DYNAMIC HOLD
        if is_hold:
            last_played = next((a for a in reversed(self.history[:-1]) if a < 36), -1)
            if last_played != -1 and (last_played % 12) in chord_notes_set:
                if self.current_action_duration <= 4:
                    reward += 1.2  # Αυξήθηκε για να προτιμάει Hold αντί για Repetition
                elif self.current_action_duration <= 8:
                    reward += 0.5
                else:
                    reward -= 1.0
            else:
                reward -= 1.0

        # 7. REST
        if is_rest:
            if self.consecutive_notes >= 4:
                reward += 2.0
            elif self.consecutive_notes == 1:
                reward -= 0.8
            elif self.current_action_duration > 6:
                reward -= 1.0
            else:
                reward += 0.1

        return reward