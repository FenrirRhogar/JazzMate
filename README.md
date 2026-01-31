# Project Evolution: AI Jazz Improvisation Agent

This document outlines the iterative improvements made to the `jazz_env.py` reinforcement learning environment to enhance the musical quality of the AI's improvisations.

## 1. Enhanced Loop Detection

*   **Problem:** The agent was getting stuck in short, repetitive melodic loops (e.g., A-B-A-B).
*   **Solution:** The initial loop detection, which only checked for 3-note repetitions, was expanded. The system now detects and penalizes 2, 3, and 4-note loops with increasing severity, forcing the agent to find more varied patterns.

## 2. Anti-Spam & Large Leap Penalties

*   **Problem:** The agent would often spam the same note or repeatedly jump between two distant notes (e.g., G5 and D4).
*   **Solution:**
    *   A bug was fixed where "hold" actions would incorrectly reset the note-spamming counter. A new mechanism (`last_note_played`) was introduced for more robust spam detection.
    *   The penalty for large, un-melodic leaps between notes was significantly increased to encourage smoother melodic lines.

## 3. Encouraging Musical Riffs

*   **Problem:** After the previous fixes, the agent became too cautious, playing only short notes and pausing frequently.
*   **Solution:** A "Riff Bonus" was introduced. The agent now receives a positive reward for playing a sequence of 4 or more *different* notes, directly incentivizing the creation of melodic runs. The "fatigue" penalty was also softened to allow these longer phrases to form.

## 4. Teaching Musical Phrasing ("Breathing")

*   **Problem:** The Riff Bonus made the agent's playing too dense and relentless, with insufficient pauses.
*   **Solution:** A "phrasing" mechanic was implemented. The agent now receives a significant reward for resting immediately *after* completing a riff. This teaches the model to "breathe" by creating musical phrases followed by pauses, achieving a more natural balance between complexity and silence.

---

# Εξέλιξη Project: AI Agent Τζαζ Αυτοσχεδιασμού

Αυτό το έγγραφο περιγράφει τις διαδοχικές βελτιώσεις που έγιναν στο περιβάλλον reinforcement learning `jazz_env.py` για την ενίσχυση της μουσικής ποιότητας των αυτοσχεδιασμών του AI.

## 1. Βελτιωμένη Ανίχνευση Επανάληψης

*   **Πρόβλημα:** Ο agent "κολλούσε" σε σύντομες, επαναλαμβανόμενες μελωδικές φράσεις (π.χ., A-B-A-B).
*   **Λύση:** Η αρχική ανίχνευση επανάληψης, που έλεγχε μόνο για μοτίβα 3 νοτών, επεκτάθηκε. Το σύστημα πλέον ανιχνεύει και τιμωρεί επαναλήψεις 2, 3 και 4 νοτών με αυξανόμενη αυστηρότητα, αναγκάζοντας τον agent να αναζητά πιο ποικίλα μοτίβα.

## 2. Κατάργηση "Spam" και Τιμωρία Μεγάλων Πηδημάτων

*   **Πρόβλημα:** Ο agent συχνά έπαιζε την ίδια νότα συνεχόμενα (spamming) ή πηδούσε επανειλημμένα μεταξύ δύο απόμακρων νοτών (π.χ., G5 και D4).
*   **Λύση:**
    *   Διορθώθηκε ένα σφάλμα όπου η ενέργεια "hold" μηδένιζε εσφαλμένα τον μετρητή spamming. Εισήχθη ένας νέος μηχανισμός (`last_note_played`) για πιο αξιόπιστη ανίχνευση spam.
    *   Η ποινή για μεγάλα, μη-μελωδικά πηδήματα μεταξύ νοτών αυξήθηκε σημαντικά για να ενθαρρύνει πιο ομαλές μελωδικές γραμμές.

## 3. Ενθάρρυνση Μουσικών Φράσεων (Riffs)

*   **Πρόβλημα:** Μετά τις προηγούμενες διορθώσεις, ο agent έγινε υπερβολικά προσεκτικός, παίζοντας μόνο σύντομες νότες και συχνές παύσεις.
*   **Λύση:** Εισήχθη ένα "Riff Bonus". Ο agent πλέον λαμβάνει θετική ανταμοιβή όταν παίζει μια ακολουθία 4 ή περισσότερων *διαφορετικών* νοτών, δίνοντας άμεσο κίνητρο για τη δημιουργία μελωδικών περασμάτων. Η ποινή "κόπωσης" (fatigue) επίσης μειώθηκε για να επιτρέπει τη δημιουργία αυτών των μεγαλύτερων φράσεων.

## 4. Διδασκαλία Μουσικής Φρασεολογίας ("Αναπνοή")

*   **Πρόβλημα:** Το Riff Bonus έκανε το παίξιμο του agent υπερβολικά "πυκνό" και ασταμάτητο, χωρίς αρκετές παύσεις.
*   **Λύση:** Υλοποιήθηκε ένας μηχανισμός "φρασεολογίας" (phrasing). Ο agent τώρα λαμβάνει σημαντική ανταμοιβή όταν κάνει παύση αμέσως *μετά* την ολοκλήρωση ενός riff. Αυτό διδάσκει στο μοντέλο να "αναπνέει", δημιουργώντας μουσικές φράσεις που ακολουθούνται από παύσεις, επιτυγχάνοντας μια πιο φυσική ισορροπία μεταξύ πολυπλοκότητας και σιωπής.

---

## Installation and Usage

These instructions are intended for a Debian-based Linux distribution (like Ubuntu).

### 1. Environment Setup

**Activate the Virtual Environment:**
Before you begin, activate the Python virtual environment.
```bash
source .venv/bin/activate
```

### 2. Install Dependencies

**Install Python Packages:**
Install the required Python libraries using pip.
```bash
pip install -r requirements.txt
```

**Install FluidSynth:**
FluidSynth is required to generate audio from the MIDI output.
```bash
sudo apt-get update
sudo apt-get install fluidsynth
```
*You will also need a SoundFont file. The `play_jazz.py` script is configured to use `FluidR3_GM.sf2`, which can be downloaded online.*

### 3. Running the Project

**Start FluidSynth:**
Open a new, separate terminal and run FluidSynth. This will act as a virtual synthesizer for our project to connect to.
```bash
fluidsynth -a pulseaudio -m alsa_seq -s -a 'at'/usr/share/soundfonts/FluidR3_GM.sf2
```
*Leave this terminal open while you are using the application.*

**Train the Agent:**
To train a new model from scratch, run the training script. This will delete any existing model and save a new one as `jazz_dqn_model.zip`.
```bash
python train.py
```

**Play and Improvise:**
Once you have a trained model, run the player script to listen to the AI's improvisation or jam with it using a MIDI controller.
```bash
python play_jazz.py
```

---

## Εγκατάσταση και Χρήση

Αυτές οι οδηγίες προορίζονται για μια διανομή Linux βασισμένη σε Debian (όπως το Ubuntu).

### 1. Προετοιμασία Περιβάλλοντος

**Ενεργοποίηση Εικονικού Περιβάλλοντος:**
Πριν ξεκινήσετε, ενεργοποιήστε το εικονικό περιβάλλον της Python.
```bash
source .venv/bin/activate
```

### 2. Εγκατάσταση Εξαρτήσεων

**Εγκατάσταση Πακέτων Python:**
Εγκαταστήστε τις απαραίτητες βιβλιοθήκες Python χρησιμοποιώντας το pip.
```bash
pip install -r requirements.txt
```

**Εγκατάσταση FluidSynth:**
Το FluidSynth είναι απαραίτητο για την παραγωγή ήχου από το MIDI που παράγει το πρόγραμμα.
```bash
sudo apt-get update
sudo apt-get install fluidsynth
```
*Θα χρειαστείτε επίσης ένα αρχείο SoundFont. Το script `play_jazz.py` είναι ρυθμισμένο να χρησιμοποιεί το `FluidR3_GM.sf2`, το οποίο μπορείτε να κατεβάσετε από το διαδίκτυο.*

### 3. Εκτέλεση του Project

**Εκκίνηση του FluidSynth:**
Ανοίξτε ένα νέο, ξεχωριστό τερματικό και εκτελέστε το FluidSynth. Αυτό θα λειτουργήσει ως ένας εικονικός συνθεσάιζερ στον οποίο θα συνδεθεί το πρόγραμμά μας.
```bash
fluidsynth -a pulseaudio -m alsa_seq -s -a 'at'/usr/share/soundfonts/FluidR3_GM.sf2
```
*Αφήστε αυτό το τερματικό ανοιχτό καθ' όλη τη διάρκεια χρήσης της εφαρμογής.*

**Εκπαίδευση του Πράκτορα:**
Για να εκπαιδεύσετε ένα νέο μοντέλο από την αρχή, εκτελέστε το script εκπαίδευσης. Αυτό θα διαγράψει οποιοδήποτε υπάρχον μοντέλο και θα αποθηκεύσει ένα νέο ως `jazz_dqn_model.zip`.
```bash
python train.py
```

**Αναπαραγωγή και Αυτοσχεδιασμός:**
Μόλις έχετε ένα εκπαιδευμένο μοντέλο, εκτελέστε το script αναπαραγωγής για να ακούσετε τον αυτοσχεδιασμό του AI ή για να τζαμάρετε μαζί του χρησιμοποιώντας ένα MIDI controller.
```bash
python play_jazz.py
```