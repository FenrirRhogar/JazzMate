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

# === CONFIGURATION ===
MODEL_PATH = "jazz_model"
MIDI_FILENAME = "output/jam_session.mid"
WAV_FILENAME = "output/jam_session.wav"
MP3_FILENAME = "output/jam_session.mp3"
SOUNDFONT = "/usr/share/soundfonts/FluidR3_GM.sf2"

# Timing settings - 16th notes at 90 BPM
BPM = 90
STEPS_TO_PLAY = 128 * 4  # Total steps (32 bars at 16 steps per bar)
BASE_STEP_DURATION = 60 / BPM / 4  # Duration of each 16th note in seconds
TICKS_PER_STEP = 120  # MIDI ticks per step

# Piano chord voicings for left hand accompaniment
PIANO_VOICINGS = {
    "Cm7": [36, 39, 43, 46], "F7": [29, 33, 39, 42],
    "BbMaj7": [34, 38, 41, 45], "EbMaj7": [27, 31, 38, 43],
    "Am7b5": [33, 36, 39, 43], "D7": [38, 42, 45, 48],
    "Gm": [31, 34, 38, 41], "Dm7": [38, 41, 45, 48],
    "G7": [31, 35, 38, 41], "CMaj7": [36, 40, 43, 47],
    "C7b9": [36, 40, 46, 49], "Fdim7": [29, 32, 35, 38],
    "Bb6": [34, 38, 41, 43], "E7alt": [28, 32, 38, 40]
}

# Map MIDI note roots to chord names for jam mode
ROOT_TO_CHORD = {
    0: "Cm7", 1: "C7b9", 2: "D7", 3: "EbMaj7",
    4: "E7alt", 5: "F7", 6: "Fdim7", 7: "Gm",
    8: "Am7b5", 9: "Am7b5", 10: "BbMaj7", 11: "G7"
}

# --- SETUP ---
print(f"Loading Model: {MODEL_PATH}...")
try:
    env = JazzImprovisationEnv()
    model = DQN.load(MODEL_PATH)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

# ==========================================
# --- 1. AUDIO OUTPUT AUTO-SELECT ---
# ==========================================
print("\n--- 🎛️ SYSTEM CONFIG ---")
try:
    outputs = mido.get_output_names()
except:
    outputs = []

# Look for FluidSynth or other software synth automatically
output_port_name = next((n for n in outputs if "FLUID" in n or "Synth" in n), outputs[0] if outputs else None)
out_port = mido.open_output(output_port_name) if output_port_name else None

if out_port:
    print(f"🔊 Audio Output: {output_port_name}")
else:
    print("❌ ERROR: No FluidSynth/Audio Output found!")

# ==========================================
# --- 2. MIDI INPUT PRIORITY LOGIC ---
# ==========================================
try:
    inputs = mido.get_input_names()
except:
    inputs = []

print("\n🎹 Scanning for MIDI Controllers...")
input_port_name = None

# Priority: Hardware controllers > VMPK (virtual keyboard) > Fallback
hw_keywords = ["LPD8", "Keystation", "Arturia", "Akai", "USB", "MIDI 1"]

# 1. Hardware Search - collect all hardware devices
hardware_devices = []
for name in inputs:
    # Skip VMPK and Through ports during hardware detection
    if any(kw in name for kw in hw_keywords) and "VMPK" not in name and "Midi Through" not in name:
        hardware_devices.append(name)

# If hardware found, let user choose
if hardware_devices:
    print(f"\n🎛️  Found {len(hardware_devices)} hardware device(s):")
    for i, device in enumerate(hardware_devices, 1):
        print(f"   {i}. {device}")

    if len(hardware_devices) == 1:
        print(f"\nUse this device? (y/n): ", end="")
        choice = input().strip().lower()
        if choice == 'y' or choice == 'yes' or choice == '':
            input_port_name = hardware_devices[0]
            print(f"✅ Selected: {input_port_name}")
        else:
            print("⏭️  Skipping hardware...")
    else:
        print(f"\nSelect device (1-{len(hardware_devices)}) or 0 to skip: ", end="")
        try:
            choice = int(input().strip())
            if 1 <= choice <= len(hardware_devices):
                input_port_name = hardware_devices[choice - 1]
                print(f"✅ Selected: {input_port_name}")
            else:
                print("⏭️  Skipping hardware...")
        except ValueError:
            print("⏭️  Invalid input, skipping hardware...")

# 2. VMPK Search
if not input_port_name:
    input_port_name = next((n for n in inputs if "VMPK" in n), None)
    if input_port_name: print(f"   -> VMPK Found: {input_port_name}")

# 3. Fallback
if not input_port_name and inputs:
    input_port_name = next((n for n in inputs if "Midi Through" in n), inputs[0])
    print(f"   -> Fallback: {input_port_name}")


# --- CONNECT INPUT ---
# Callback function for Jam Mode - translates incoming MIDI notes to chord changes
def midi_callback(msg):
    if msg.type == 'note_on' and msg.velocity > 0:
        root = msg.note % 12
        new_chord = ROOT_TO_CHORD.get(root, "Cm7")
        try:
            env.set_manual_chord(new_chord)
            print(f"🎹 USER: {msg.note} -> \033[93m{new_chord}\033[0m")
        except AttributeError:
            pass  # In case env hasn't been updated yet


in_port = None
if input_port_name:
    try:
        # Open with callback for immediate response
        in_port = mido.open_input(input_port_name, callback=midi_callback)
        print(f"✅ CONNECTED INPUT: \033[92m{input_port_name}\033[0m")
    except Exception as e:
        print(f"❌ Failed to open input: {e}")
else:
    print("⚠️  No MIDI Input found.")

# ==========================================
# --- 3. MENU INTERFACE ---
# ==========================================
print("\n" + "=" * 30)
print("      JAZZMATE SESSION")
print("=" * 30)

# Question 1: Who controls the chord progression?
print("\n[1/2] Who selects the chords?")
print("  1. System (Random automatic progression)")
print("  2. User (Jam Mode with MIDI)")
mode_choice = input(">> Choice (1 or 2): ").strip()

MANUAL_CONTROL = (mode_choice == '2')

if MANUAL_CONTROL and not in_port:
    print("\n⚠️  WARNING: You chose Jam Mode but no controller was found!")
    print("   Chords will stay stuck on the initial one (Cm7).")

# Question 2: What backing style?
print("\n[2/2] What backing style (Piano) do you want?")
print("  1. Simple (Block Chords)")
print("  2. Arpeggio (Rhythmic Arpeggios)")
style_choice = input(">> Choice (1 or 2): ").strip()

STYLE = 'ARPEGGIO' if style_choice == '2' else 'SIMPLE'

print("\n🚀 STARTING SESSION...")
if MANUAL_CONTROL:
    print("🎹 Play notes on your controller now!")

# ==========================================
# --- SETUP MIDI FILE ---
# ==========================================
mid = MidiFile(ticks_per_beat=480)
track_solo = MidiTrack()
mid.tracks.append(track_solo)
track_backing = MidiTrack()
mid.tracks.append(track_backing)
meta_tempo = mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM))
track_solo.append(meta_tempo)
track_backing.append(meta_tempo)
# Set both tracks to piano (program 0)
track_solo.append(Message('program_change', channel=0, program=0))
track_backing.append(Message('program_change', channel=1, program=0))

if out_port:
    out_port.send(Message('program_change', channel=0, program=0))
    out_port.send(Message('program_change', channel=1, program=0))

# ==========================================
# --- MAIN LOOP ---
# ==========================================
obs, _ = env.reset()
active_note = None
active_chord_notes = []
active_arp_note = None
current_chord_name = "Cm7"
file_chord_notes = []
steps_since_chord_change = 0

try:
    for step in range(STEPS_TO_PLAY):
        # 1. AGENT PREDICTION
        action, _ = model.predict(obs, deterministic=False)

        # Apply swing timing - long on beats 1 and 3, short on 2 and 4
        is_swing_long = (step % 2 == 0)
        swing_factor = 1.3 if is_swing_long else 0.7
        current_step_ticks = int(TICKS_PER_STEP * swing_factor)
        current_step_time = BASE_STEP_DURATION * swing_factor

        is_note = action < 36
        is_rest = action == 36
        is_hold = action == 37
        note_val = 48 + int(action) if is_note else None

        env_chord = env.current_chord_name
        chord_notes = PIANO_VOICINGS.get(env_chord, [36, 40, 43])

        # 2. LEFT HAND (BACKING) LOGIC
        if STYLE == 'SIMPLE':
            # --- BLOCK CHORDS ---
            # Play a new chord only when the chord name changes (from auto or manual input)
            # or if it's the first step
            if env_chord != current_chord_name or step == 0:
                if out_port:
                    for n in active_chord_notes:
                        out_port.send(Message('note_off', channel=1, note=n, velocity=0))
                    for n in chord_notes:
                        vel = random.randint(80, 95)
                        out_port.send(Message('note_on', channel=1, note=n, velocity=vel))
                    active_chord_notes = chord_notes

                # File Logic
                if file_chord_notes:
                    duration_ticks = steps_since_chord_change * TICKS_PER_STEP
                    track_backing.append(
                        Message('note_off', channel=1, note=file_chord_notes[0], velocity=0, time=duration_ticks))
                    for n in file_chord_notes[1:]:
                        track_backing.append(Message('note_off', channel=1, note=n, velocity=0, time=0))

                for n in chord_notes:
                    track_backing.append(Message('note_on', channel=1, note=n, velocity=90, time=0))

                file_chord_notes = chord_notes
                steps_since_chord_change = 0
                current_chord_name = env_chord

            steps_since_chord_change += 1

        elif STYLE == 'ARPEGGIO':
            # --- ARPEGGIATOR ---
            current_chord_name = env_chord

            # Stop previous arp note
            if active_arp_note is not None:
                if out_port: out_port.send(Message('note_off', channel=1, note=active_arp_note, velocity=0))
                track_backing.append(
                    Message('note_off', channel=1, note=active_arp_note, velocity=0, time=current_step_ticks))
                active_arp_note = None
            else:
                track_backing.append(Message('note_off', channel=1, note=0, velocity=0, time=current_step_ticks))

            # Play new note every 2 steps (8th notes)
            if step % 2 == 0:
                note_idx = (step // 2) % len(chord_notes)
                arp_note_val = chord_notes[note_idx]
                vel = random.randint(85, 100)
                if out_port: out_port.send(Message('note_on', channel=1, note=arp_note_val, velocity=vel))
                track_backing.append(Message('note_on', channel=1, note=arp_note_val, velocity=vel, time=0))
                active_arp_note = arp_note_val
            else:
                track_backing.append(Message('note_off', channel=1, note=0, velocity=0, time=0))

        # 3. RIGHT HAND (SOLO) LOGIC
        if out_port:
            if active_note is not None and not is_hold:
                out_port.send(Message('note_off', channel=0, note=active_note, velocity=0))
                active_note = None

            if is_note:
                # Adjust velocity based on pitch (higher notes = louder for clarity)
                pitch_boost = (note_val - 60) // 2
                base_vel = random.randint(110, 127)
                final_vel = min(127, max(1, base_vel + pitch_boost))
                out_port.send(Message('note_on', channel=0, note=note_val, velocity=final_vel))
                active_note = note_val

                note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                octave = (action // 12) + 3
                name = note_names[action % 12]
                bar = (step // 16) + 1

                # Always display what the agent is playing
                prefix = "🎷 AGENT:" if MANUAL_CONTROL else "Melody:"
                print(f"Bar {bar} | Chord: {current_chord_name:7s} | {prefix} \033[96m{name}{octave}\033[0m")

            elif is_rest:
                prefix = "🎷 AGENT:" if MANUAL_CONTROL else "Melody:"
                print(f"Bar {(step // 16) + 1} | Chord: {current_chord_name:7s} | {prefix} ---")
            elif is_hold:
                prefix = "🎷 AGENT:" if MANUAL_CONTROL else "Melody:"
                print(f"Bar {(step // 16) + 1} | Chord: {current_chord_name:7s} | {prefix} ...")

        # 4. FILE SOLO LOGIC
        if is_note:
            track_solo.append(Message('note_on', channel=0, note=note_val, velocity=110, time=0))
            track_solo.append(Message('note_off', channel=0, note=note_val, velocity=0, time=current_step_ticks))
        else:
            track_solo.append(Message('note_off', channel=0, note=0, velocity=0, time=current_step_ticks))

        if out_port: time.sleep(current_step_time)

        # 5. STEP ENVIRONMENT
        if MANUAL_CONTROL:
            # In manual mode, the chord only changes via the callback
            # We step to advance time/history, but keep the user's chord selection
            saved_chord = env.current_chord_name
            obs, _, _, _, _ = env.step(action)
            env.current_chord_name = saved_chord  # Restore user's chord choice
        else:
            # In auto mode, let the environment change chords
            obs, _, done, _, _ = env.step(action)
            if done: obs, _ = env.reset()

except KeyboardInterrupt:
    print("\nStopping...")

# Cleanup - stop all playing notes
if out_port:
    if active_note: out_port.send(Message('note_off', channel=0, note=active_note, velocity=0))
    for n in active_chord_notes: out_port.send(Message('note_off', channel=1, note=n, velocity=0))
    if active_arp_note: out_port.send(Message('note_off', channel=1, note=active_arp_note, velocity=0))
    out_port.close()
if in_port: in_port.close()

# Close file buffers
if file_chord_notes:
    duration_ticks = steps_since_chord_change * TICKS_PER_STEP
    track_backing.append(Message('note_off', channel=1, note=file_chord_notes[0], velocity=0, time=duration_ticks))
    for n in file_chord_notes[1:]:
        track_backing.append(Message('note_off', channel=1, note=n, velocity=0, time=0))

mid.save(MIDI_FILENAME)
print(f"\n✅ MIDI saved to {MIDI_FILENAME}")

print("\n--- RENDERING AUDIO ---")
if os.path.exists(SOUNDFONT):
    try:
        # Convert MIDI to WAV using FluidSynth, then to MP3
        subprocess.run(["fluidsynth", "-ni", "-g", "1.5", "-F", WAV_FILENAME, SOUNDFONT, MIDI_FILENAME],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-i", WAV_FILENAME, "-acodec", "libmp3lame", "-q:a", "2", MP3_FILENAME],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ \033[92mSUCCESS: {MP3_FILENAME} created!\033[0m")
        os.remove(WAV_FILENAME)
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print(f"❌ SoundFont not found.")