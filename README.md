# Jazz Music Generation with Deep Q-Learning

This project uses a Deep Q-Learning (DQN) model to generate jazz music. The agent is trained in a custom environment to compose jazz solos.

## Files

*   `jazz_env.py`: The custom OpenAI Gym environment for the jazz generation task.
*   `train.py`: The script to train the DQN agent.
*   `play_jazz.py`: A script to play a generated jazz solo.

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

## Repository Cleanup
Certain files have been removed from the git history to reduce the repository size. These files are now listed in the `.gitignore` file and will not be tracked going forward.
