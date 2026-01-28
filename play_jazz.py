import gymnasium as gym
from stable_baselines3 import DQN
from jazz_env import JazzImprovisationEnv
import mido
from mido import Message, MidiFile, MidiTrack
import time
import sys
import random
import subprocess
import os

# --- ΡΥΘΜΙΣΕΙΣ ---
MODEL_PATH = "jazz_dqn_model"
MIDI_FILENAME = "random_jazz_session.mid"
WAV_FILENAME = "random_jazz_session.wav"
MP3_FILENAME = "kalo.mp3"
SOUNDFONT = "/usr/share/soundfonts/FluidR3_GM.sf2"

BPM = 90  # Λίγο πιο αργά για να ακουστεί το Swing
STEPS_TO_PLAY = 128 * 2
BASE_STEP_DURATION = 60 / BPM / 4
TICKS_PER_STEP = 120

PIANO_VOICINGS = {
    "Cm7": [48, 51, 58], "F7": [41, 54, 57],
    "BbMaj7": [46, 50, 53, 57], "EbMaj7": [39, 55, 58],
    "Am7b5": [45, 48, 55], "D7": [50, 54, 60],
    "Gm": [43, 46, 53, 58], "Dm7": [50, 53, 57, 60],
    "G7": [43, 47, 50, 53], "CMaj7": [48, 52, 55, 59]
}

print(f"Loading Model: {MODEL_PATH}...")
try:
    env = JazzImprovisationEnv()
    model = DQN.load(MODEL_PATH)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

mid = MidiFile(ticks_per_beat=480)
track_solo = MidiTrack()
mid.tracks.append(track_solo)
track_backing = MidiTrack()
mid.tracks.append(track_backing)

meta_tempo = mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM))
track_solo.append(meta_tempo)
track_backing.append(meta_tempo)

track_solo.append(Message('program_change', channel=0, program=0, time=0))
track_backing.append(Message('program_change', channel=1, program=0, time=0))

try:
    outputs = mido.get_output_names()
except:
    outputs = []
port_name = next((n for n in outputs if "FLUID" in n or "Synth" in n), outputs[0] if outputs else None)
port = mido.open_output(port_name) if port_name else None
if port: print(f"✅ Connected to: {port_name}")

print("\n--- RECORDING WITH SWING FEEL ---")
obs, _ = env.reset()

active_note = None
active_chord_notes = []
file_chord_notes = []
current_chord_name = ""
steps_since_chord_change = 0

if port:
    port.send(Message('program_change', channel=0, program=0))
    port.send(Message('program_change', channel=1, program=0))

for step in range(STEPS_TO_PLAY):
    action, _ = model.predict(obs, deterministic=False)

    # --- SWING LOGIC (HUMANIZER) ---
    # On-beat (even step): Long (1.3x)
    # Off-beat (odd step): Short (0.7x)
    is_swing_long = (step % 2 == 0)
    swing_factor = 1.3 if is_swing_long else 0.7

    current_step_ticks = int(TICKS_PER_STEP * swing_factor)
    current_step_time = BASE_STEP_DURATION * swing_factor

    is_note = action < 36
    is_rest = action == 36
    is_hold = action == 37
    note_val = 48 + int(action) if is_note else None

    env_chord = env.current_chord_name

    # --- BACKING TRACK ---
    if env_chord != current_chord_name:
        if port:
            for n in active_chord_notes:
                port.send(Message('note_off', channel=1, note=n, velocity=0))
            new_notes = PIANO_VOICINGS.get(env_chord, [48, 52, 55])
            for n in new_notes:
                vel = random.randint(45, 55)
                port.send(Message('note_on', channel=1, note=n, velocity=vel))
            active_chord_notes = new_notes

        if file_chord_notes:
            # Backing isn't swung per step, it's held, so we just sum up real time
            # Here we simplify and put it on grid, backing doesn't need heavy swing
            track_backing.append(Message('note_off', channel=1, note=file_chord_notes[0], velocity=0,
                                         time=steps_since_chord_change * TICKS_PER_STEP))
            for n in file_chord_notes[1:]:
                track_backing.append(Message('note_off', channel=1, note=n, velocity=0, time=0))

        new_file_notes = PIANO_VOICINGS.get(env_chord, [48, 52, 55])
        for n in new_file_notes:
            track_backing.append(Message('note_on', channel=1, note=n, velocity=50, time=0))

        file_chord_notes = new_file_notes
        current_chord_name = env_chord
        steps_since_chord_change = 0

    steps_since_chord_change += 1

    # --- SOLO TRACK ---
    if port:
        if active_note is not None and not is_hold:
            port.send(Message('note_off', channel=0, note=active_note, velocity=0))
            active_note = None

        if is_note:
            # HUMAN VELOCITY
            # Higher pitch = slightly louder
            pitch_boost = (note_val - 60) // 2
            # Downbeat accent (start of bar)
            beat_accent = 10 if (step % 16 == 0) else 0

            base_vel = random.randint(80, 95)
            final_vel = min(127, max(1, base_vel + pitch_boost + beat_accent))

            port.send(Message('note_on', channel=0, note=note_val, velocity=final_vel))
            active_note = note_val

            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = (action // 12) + 3
            name = note_names[action % 12]
            bar = (step // 16) + 1
            print(f"Bar {bar} | Chord: {current_chord_name:7s} | \033[96m{name}{octave}\033[0m")

        elif is_rest:
            print(f"Bar {(step // 16) + 1} | Chord: {current_chord_name:7s} | ---")
        elif is_hold:
            print(f"Bar {(step // 16) + 1} | Chord: {current_chord_name:7s} | ...")

    # FILE RECORDING (APPLYING SWING TO MIDI TICKS)
    if is_note:
        track_solo.append(Message('note_on', channel=0, note=note_val, velocity=90, time=0))
        track_solo.append(Message('note_off', channel=0, note=note_val, velocity=0, time=current_step_ticks))
    else:
        track_solo.append(Message('note_off', channel=0, note=0, velocity=0, time=current_step_ticks))

    if port: time.sleep(current_step_time)

    obs, _, done, _, _ = env.step(action)
    if done: obs, _ = env.reset()

# Cleanup
if port:
    if active_note: port.send(Message('note_off', channel=0, note=active_note, velocity=0))
    for n in active_chord_notes: port.send(Message('note_off', channel=1, note=n, velocity=0))
    port.close()

if file_chord_notes:
    track_backing.append(Message('note_off', channel=1, note=file_chord_notes[0], velocity=0,
                                 time=steps_since_chord_change * TICKS_PER_STEP))
    for n in file_chord_notes[1:]:
        track_backing.append(Message('note_off', channel=1, note=n, velocity=0, time=0))

mid.save(MIDI_FILENAME)
print(f"\n✅ MIDI saved to {MIDI_FILENAME}")

# --- MP3 RENDERING ---
print("\n--- RENDERING AUDIO ---")
if os.path.exists(SOUNDFONT):
    try:
        subprocess.run(["fluidsynth", "-ni", "-g", "1.0", "-F", WAV_FILENAME, SOUNDFONT, MIDI_FILENAME],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-i", WAV_FILENAME, "-acodec", "libmp3lame", "-q:a", "2", MP3_FILENAME],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ \033[92mSUCCESS: {MP3_FILENAME} created!\033[0m")
        os.remove(WAV_FILENAME)
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print(f"❌ SoundFont not found.")