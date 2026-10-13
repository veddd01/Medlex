"""Training script for RL retrieval optimization."""
import argparse
import logging
import os
from pathlib import Path

from rl.env import RAGOptimizationEnv
from rl.policy import FixedPolicy, RandomPolicy, HeuristicPolicy, ContextualBanditPolicy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--use-mock", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    eval_file = Path("eval/questions.json")
    if not eval_file.exists():
        logger.error(f"Eval file {eval_file} not found.")
        return

    env = RAGOptimizationEnv(str(eval_file), use_mock=args.use_mock)
    
    # Calculate obs dim for bandit
    # len: 1, type: 4, scores: 5, mean: 1, max: 1, num_above: 1 = 13
    obs_dim = 13
    action_dims = [3, 2, 3, 2]
    
    policies = {
        "fixed": FixedPolicy(),
        "random": RandomPolicy(env.action_space),
        "heuristic": HeuristicPolicy(),
        "bandit": ContextualBanditPolicy(obs_dim, action_dims)
    }

    results = {}

    for name, policy in policies.items():
        logger.info(f"Evaluating/Training {name}...")
        total_rewards = []
        
        episodes = args.episodes if name == "bandit" else 1 # baselines don't need training
        
        for ep in range(episodes):
            obs, _ = env.reset(seed=args.seed)
            ep_reward = 0
            terminated = False
            
            while not terminated:
                action = policy.select_action(obs)
                next_obs, reward, terminated, _, info = env.step(action)
                
                if name == "bandit":
                    policy.update(obs, action, reward)
                    
                obs = next_obs
                ep_reward += reward
                
            if name == "bandit" and (ep + 1) % 10 == 0:
                logger.info(f"Episode {ep+1}: {ep_reward:.2f}")
                
            if ep == episodes - 1:
                total_rewards.append(ep_reward)

        results[name] = sum(total_rewards) / len(total_rewards)
        
        if name == "bandit":
            os.makedirs("rl/results", exist_ok=True)
            policy.save("rl/results/bandit_weights.npz")

    logger.info("--- Results ---")
    for name, score in results.items():
        logger.info(f"{name}: {score:.2f}")

if __name__ == "__main__":
    train()
