# JazzMate 🎷

**An Autonomous Jazz Improvisation Agent using Deep Reinforcement Learning**

JazzMate is an intelligent musical agent that learns to generate jazz solos in real-time through Deep Q-Learning (DQN). The system responds dynamically to chord progressions and can interact with human musicians via MIDI controllers.

---

## 🎯 Project Overview

This project implements an autonomous agent capable of:
- **Real-time jazz improvisation** with harmonic awareness
- **Interactive jamming** with human musicians via MIDI input
- **Musical phrasing** through learned reward shaping
- **Anti-repetition mechanisms** to avoid monotonous patterns
- **Swing feel** and humanized playback

The agent is trained using **Deep Q-Networks (DQN)** from Stable-Baselines3, with a custom Gymnasium environment that encodes musical theory into the reward function.

---

## 📁 Project Structure

```
JazzMate/
├── jazz_env.py          # Custom RL environment (MDP definition)
├── train.py             # Training script with monitoring
├── play_jazz.py         # Interactive playback system
├── report.pdf           # Full technical report (LaTeX)
├── requirements.txt     # Python dependencies
└── README.md
```

---

## 🧠 Technical Architecture

### Environment (MDP Specification)

**State Space** (`Dict` observation):
- **`chord_tones`**: Multi-hot encoding (12 dimensions) of current chord notes
- **`step_progress`**: Position within the piece (0→1)
- **`last_action`**: Previous note/rest/hold action
- **`held_duration`**: How long the current note has been sustained
- **`style_seed`**: Random variation factor for diversity

**Action Space** (38 discrete actions):
- Actions 0-35: Notes spanning 3 octaves (C3 to B5)
- Action 36: Rest (silence)
- Action 37: Hold (sustain current note)

**Reward Function** 

### Algorithm

- **Model**: Deep Q-Network (DQN) with `MultiInputPolicy`
- **Framework**: Stable-Baselines3
- **Training Steps**: 200,000 timesteps
- **Learning Rate**: 1e-4
- **Buffer Size**: 50,000
- **Exploration**: Decaying ε-greedy (40% → 5%)

---

## 🎵 Reward Shaping Evolution

The reward function underwent several iterations to balance musical correctness with creative freedom:

### 1. **Harmonic Compliance**
- **+1.0** for notes within the current chord
- **-0.6** for out-of-chord notes

### 2. **Melodic Flow**
- **+0.8** for small intervals (1-2 semitones) → smooth lines
- **-1.5** for large leaps (>9 semitones) → penalize disjunct motion

### 3. **Anti-Spam Mechanism**
Prevents the agent from repeating the same note:
```python
if exact_note_repeats == 1:  reward -= 2.0
elif exact_note_repeats >= 2: reward -= 10.0  # Severe penalty
```

### 4. **Loop Detection**
Detects and penalizes repetitive patterns:
- 2-note loops (A-B-A-B): **-5.0**
- 3-note loops (A-B-C-A-B-C): **-10.0**
- 4-note loops: **-15.0**

### 5. **Riff Bonus**
Encourages melodic phrases with varied notes:
- 4 consecutive different notes: **+2.5**
- 5+ consecutive different notes: **+4.0**

### 6. **Musical Phrasing**
Teaches the agent to "breathe":
- **+3.0** for resting after a successful riff (4+ varied notes)
- Encourages natural phrase boundaries

---

## 🚀 Installation & Usage

### Prerequisites

This project is designed for **Linux (Debian-based)** systems like Ubuntu.

### 1. Setup Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

**Python Packages:**
```bash
pip install -r requirements.txt
```

**System Dependencies (FluidSynth):**
```bash
sudo apt-get update
sudo apt-get install fluidsynth fluid-soundfont-gm
```

**Download SoundFont (if not included):**
```bash
sudo apt-get install fluid-soundfont-gm
# This installs to /usr/share/soundfonts/FluidR3_GM.sf2
```

### 3. Running the Project

#### Start FluidSynth (Audio Backend)

Open a **separate terminal** and run:
```bash
fluidsynth -a pulseaudio -m alsa_seq -s /usr/share/soundfonts/FluidR3_GM.sf2
```
*Keep this terminal open during usage.*

#### Train the Agent

To train a new model from scratch:
```bash
python train.py
```
- Deletes any existing `jazz_dqn_model.zip`
- Trains for 200k steps
- Saves model and generates `training_graph.png`

#### Play & Jam

To hear the trained agent improvise:
```bash
python play_jazz.py
```

**Interactive Options:**
1. **Auto Mode**: System generates random chord progressions
2. **Jam Mode**: Use a MIDI controller to control chord changes in real-time

**Style Options:**
1. **Simple**: Block chord accompaniment
2. **Arpeggio**: Rhythmic arpeggiated backing

**Output Files:**
- `jam_session.mid` - MIDI recording
- `jam_session.mp3` - Rendered audio

---


## 🎹 MIDI Controller Support

JazzMate automatically detects MIDI input devices with priority:

1. **Hardware Controllers** (e.g., Akai, Keystation, Arturia)
2. **Virtual MIDI Piano Keyboard (VMPK)**
3. **System MIDI Through ports**

In **Jam Mode**, play root notes on your controller to change chords dynamically:
- **C** → Cm7
- **D** → D7
- **Eb** → EbMaj7
- **F** → F7
- **G** → Gm or G7
- **A** → Am7b5
- **Bb** → BbMaj7

---


## 📝 Academic Context

**Course**: Autonomous Agents  
**Institution**: Technical University of Crete 
**Student**: Ioannis Bouritis 
**Semester**: Winter 2025-2026

---

## 🛠️ Technologies Used

- **Python 3.x**
- **Gymnasium** (OpenAI Gym successor)
- **Stable-Baselines3** (DQN implementation)
- **Mido** (MIDI I/O)
- **FluidSynth** (Audio synthesis)
- **FFmpeg** (Audio conversion)
- **Matplotlib** (Training visualization)

---