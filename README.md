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

```text
JazzMate/
├── jazz_env.py           # Custom RL environment (MDP definition)
├── train.py              # Training script with monitoring
├── play_jazz.py          # Interactive playback system
├── report.pdf            # Full technical report
├── JazzMate Presentation.pdf # Project presentation slides
├── index.html            # Web-based project summary/demo
├── requirements.txt      # Python dependencies
├── LICENSE               # Project license (MIT)
├── README.md             # Project documentation
├── training_graph.png    # Training performance visualization
├── results/              # Evaluation results
│   ├── learning_curve.png
│   └── playtest.mp4      # Video demonstration of the agent
├── training_logs/        # Training session logs
│   └── monitor.csv       # Step-by-step training metrics
└── .venv/                # Python virtual environment
```

---

## 📖 Technical Details

For comprehensive technical documentation including:
- MDP formulation and state/action space design
- Detailed reward function architecture and evolution
- Training methodology and hyperparameters
- Performance analysis and results

Please refer to [report.pdf](report.pdf).

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