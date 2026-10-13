# Phase 7: RL Retrieval Environment

This directory contains an experimental Gymnasium-style reinforcement learning environment for optimizing RAG retrieval settings.

## What this experiment is
It is an experiment to see if an RL agent (specifically a Contextual Bandit) can learn optimal retrieval parameters based on the features of an incoming question and the preliminary retrieval scores. The environment is built on top of the Phase 2 evaluation set (`eval/questions.json`).

The agent observes:
- Question length and type
- Top similarity scores from an initial retrieval pass
- Mean and max scores
- Number of chunks above a threshold

The agent takes actions on:
- `top_k` (1, 3, or 5)
- Whether to rerank (yes/no)
- `min_score` threshold (0.2, 0.3, or 0.5)
- Whether to answer or refuse

## Reward
The reward is computed based on retrieval hits (if the expected page is retrieved), keyword coverage, and correct refusals for unanswerable questions. There is an efficiency penalty for retrieving more chunks.

## How to train and evaluate
Install dependencies from `requirements.txt`. Then:

```bash
# Train the bandit model and compare with baselines
python -m rl.train --episodes 100 --seed 42 --use-mock

# Evaluate a specific policy
python -m rl.evaluate --policy heuristic
python -m rl.evaluate --policy bandit --model-path rl/results/bandit_weights.npz
```

## Expected results
The heuristic policy (which uses simple rules based on the max score) will likely beat the random policy easily. The bandit should converge to a performance near the heuristic or fixed policy, depending on the number of episodes and learning rate.

## Limitations & Honest Caveats
- **Small Evaluation Set**: The 40-question eval set limits generalization. The bandit may overfit.
- **Mock Retriever**: By default (`--use-mock`), we use a mock retriever that simulates results based on the eval set. It doesn't capture real retrieval noise from Pinecone.
- **Coarse Action Space**: Only a few options are available for each parameter.
- **Not Production RL**: This is a proof of concept. The chatbot is not "trained with RL" in production.

## Safety Constraints
**CRITICAL**: Safety constraints cannot be bypassed by the learned policy. The environment always runs `check_emergency()` on every question before the agent acts. If an emergency is detected, the environment automatically refuses, regardless of the agent's action. The medical disclaimer is always present.
