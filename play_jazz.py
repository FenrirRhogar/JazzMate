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
MIDI_FILENAME = "jam_session.mid"
WAV_FILENAME = "jam_session.wav"
MP3_FILENAME = "jam_session.mp3"
SOUNDFONT = "/usr/share/soundfonts/FluidR3_GM.sf2"

BPM = 90
STEPS_TO_PLAY = 128 * 4
BASE_STEP_DURATION = 60 / BPM / 4
TICKS_PER_STEP = 120

PIANO_VOICINGS = {
    "Cm7": [48, 51, 55, 58], "F7": [41, 45, 51, 54],
    "BbMaj7": [46, 50, 53, 57], "EbMaj7": [39, 43, 50, 55],
    "Am7b5": [45, 48, 51, 55], "D7": [50, 54, 57, 60],
    "Gm": [43, 46, 50, 53], "Dm7": [50, 53, 57, 60],
    "G7": [43, 47, 50, 53], "CMaj7": [48, 52, 55, 59],
    "C7b9": [48, 52, 58, 61], "Fdim7": [41, 44, 47, 50],
    "Bb6": [46, 50, 53, 55], "E7alt": [40, 44, 50, 52]
}

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

# Ψάχνουμε FluidSynth αυτόματα
output_port_name = next((n for n in outputs if "FLUID" in n or "Synth" in n), outputs[0] if outputs else None)
out_port = mido.open_output(output_port_name) if output_port_name else None

if out_port:
    print(f"🔊 Audio Output: {output_port_name}")
else:
    print("❌ ERROR: Δεν βρέθηκε FluidSynth/Audio Output!")

# ==========================================
# --- 2. MIDI INPUT PRIORITY LOGIC ---
# ==========================================
try:
    inputs = mido.get_input_names()
except:
    inputs = []

print("\n🎹 Scanning for MIDI Controllers...")
input_port_name = None

# Priority List (Hardware Keywords)
hw_keywords = ["LPD8", "Keystation", "Arturia", "Akai", "USB", "MIDI 1"]

# 1. Hardware Search
for name in inputs:
    # Αγνοούμε VMPK και Through σε αυτή τη φάση
    if any(kw in name for kw in hw_keywords) and "VMPK" not in name and "Midi Through" not in name:
        input_port_name = name
        print(f"   -> Hardware Found: {name}")
        break

# 2. VMPK Search
if not input_port_name:
    input_port_name = next((n for n in inputs if "VMPK" in n), None)
    if input_port_name: print(f"   -> VMPK Found: {input_port_name}")

# 3. Fallback
if not input_port_name and inputs:
    input_port_name = next((n for n in inputs if "Midi Through" in n), inputs[0])
    print(f"   -> Fallback: {input_port_name}")


# --- CONNECT INPUT ---
# Callback function for Jam Mode
def midi_callback(msg):
    if msg.type == 'note_on' and msg.velocity > 0:
        root = msg.note % 12
        new_chord = ROOT_TO_CHORD.get(root, "Cm7")
        try:
            env.set_manual_chord(new_chord)
            print(f"🎹 USER: {msg.note} -> \033[93m{new_chord}\033[0m")
        except AttributeError:
            pass  # Σε περίπτωση που το env δεν έχει ενημερωθεί ακόμα


in_port = None
if input_port_name:
    try:
        # Ανοίγουμε με callback για άμεση απόκριση
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

# Ερώτηση 1: Mode
print("\n[1/2] Ποιος επιλέγει τις συγχορδίες;")
print("  1. Το Σύστημα (Αυτόματη τυχαία σειρά)")
print("  2. Ο Χρήστης (Jam Mode με MIDI)")
mode_choice = input(">> Επιλογή (1 ή 2): ").strip()

MANUAL_CONTROL = (mode_choice == '2')

if MANUAL_CONTROL and not in_port:
    print("\n⚠️  ΠΡΟΣΟΧΗ: Διαλέξατε Jam Mode αλλά δεν βρέθηκε Controller!")
    print("   Οι συγχορδίες θα μείνουν κολλημένες στην αρχική (Cm7).")

# Ερώτηση 2: Style
print("\n[2/2] Τι στυλ συνοδείας (Πιάνο) θέλετε;")
print("  1. Simple (Block Chords)")
print("  2. Arpeggio (Ρυθμικό Άρπισμα)")
style_choice = input(">> Επιλογή (1 ή 2): ").strip()

STYLE = 'ARPEGGIO' if style_choice == '2' else 'SIMPLE'

print("\n🚀 ΕΚΚΙΝΗΣΗ SESSION...")
if MANUAL_CONTROL:
    print("🎹 Παίξε νότες στο controller σου τώρα!")

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
        # 1. AI PREDICTION
        action, _ = model.predict(obs, deterministic=False)

        is_swing_long = (step % 2 == 0)
        swing_factor = 1.3 if is_swing_long else 0.7
        current_step_ticks = int(TICKS_PER_STEP * swing_factor)
        current_step_time = BASE_STEP_DURATION * swing_factor

        is_note = action < 36
        is_rest = action == 36
        is_hold = action == 37
        note_val = 48 + int(action) if is_note else None

        env_chord = env.current_chord_name
        chord_notes = PIANO_VOICINGS.get(env_chord, [48, 52, 55])

        # 2. LEFT HAND (BACKING) LOGIC
        if STYLE == 'SIMPLE':
            # --- BLOCK CHORDS ---
            # Παίζουμε νέα συγχορδία ΜΟΝΟ αν άλλαξε το όνομα (από το Auto ή το Manual Input)
            # Ή αν είναι το πρώτο βήμα
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
                pitch_boost = (note_val - 60) // 2
                base_vel = random.randint(110, 127)
                final_vel = min(127, max(1, base_vel + pitch_boost))
                out_port.send(Message('note_on', channel=0, note=note_val, velocity=final_vel))
                active_note = note_val

                note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                octave = (action // 12) + 3
                name = note_names[action % 12]
                bar = (step // 16) + 1

                # ΠΑΝΤΑ εμφανίζουμε τι παίζει το AI
                prefix = "🎷 AI:" if MANUAL_CONTROL else "Melody:"
                print(f"Bar {bar} | Chord: {current_chord_name:7s} | {prefix} \033[96m{name}{octave}\033[0m")

            elif is_rest:
                prefix = "🎷 AI:" if MANUAL_CONTROL else "Melody:"
                print(f"Bar {(step // 16) + 1} | Chord: {current_chord_name:7s} | {prefix} ---")
            elif is_hold:
                prefix = "🎷 AI:" if MANUAL_CONTROL else "Melody:"
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
            # Στο Manual Mode, η συγχορδία αλλάζει ΜΟΝΟ από το callback
            # Κάνουμε step για να προχωρήσει το χρόνο/ιστορικό του Agent, αλλά κρατάμε τη συγχορδία σταθερή
            # (Εκτός αν άλλαξε στο ενδιάμεσο από το callback, το οποίο θα έχει ήδη ενημερώσει το env)
            saved_chord = env.current_chord_name
            obs, _, _, _, _ = env.step(action)
            env.current_chord_name = saved_chord  # Επαναφορά στην επιλογή χρήστη (το step του env μπορεί να προσπάθησε να την αλλάξει)
        else:
            # Στο Auto Mode, αφήνουμε το περιβάλλον να αλλάξει συγχορδία
            obs, _, done, _, _ = env.step(action)
            if done: obs, _ = env.reset()

except KeyboardInterrupt:
    print("\nStopping...")

# Cleanup
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