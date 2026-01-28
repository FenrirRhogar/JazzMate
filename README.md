# Jazz Music Generation with Deep Q-Learning

This project uses a Deep Q-Learning (DQN) model to generate jazz music. The agent is trained in a custom environment to compose jazz solos.

## Files

*   `jazz_env.py`: The custom OpenAI Gym environment for the jazz generation task.
*   `train.py`: The script to train the DQN agent.
*   `play_jazz.py`: A script to play a generated jazz solo.
*   `jazz_dqn_model.zip`: A pre-trained DQN model.
*   `live_jazz_piano_solo.mid`, `live_jazz_solo.mid`, `random_jazz_session.mid`: MIDI files used for training or as examples.
*   `autumn_leaves_generated.mid`: A sample of a generated MIDI file.
*   `kalo.mp3`: An audio file, likely for inspiration or comparison.
*   `Autonomous_Agents_Project.pdf`: Project documentation.

## How to Use

### Training

To train a new model, run:

```bash
python train.py
```

### Generate Music

To generate music using a pre-trained model, run:

```bash
python play_jazz.py
```
