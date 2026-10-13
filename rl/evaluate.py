"""Evaluation script for RL retrieval optimization."""
import argparse
import json
import logging
import os
from pathlib import Path

from rl.env import RAGOptimizationEnv
from rl.policy import FixedPolicy, RandomPolicy, HeuristicPolicy, ContextualBanditPolicy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def evaluate():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=str, required=True, choices=["fixed", "random", "heuristic", "bandit"])
    parser.add_argument("--model-path", type=str, default="rl/results/bandit_weights.npz")
    args = parser.parse_args()

    eval_file = Path("eval/questions.json")
    if not eval_file.exists():
        logger.error(f"Eval file {eval_file} not found.")
        return

    env = RAGOptimizationEnv(str(eval_file), use_mock=True)
    
    if args.policy == "fixed":
        policy = FixedPolicy()
    elif args.policy == "random":
        policy = RandomPolicy(env.action_space)
    elif args.policy == "heuristic":
        policy = HeuristicPolicy()
    elif args.policy == "bandit":
        policy = ContextualBanditPolicy(13, [3, 2, 3, 2])
        policy.epsilon = 0.0 # evaluate without exploration
        try:
            policy.load(args.model_path)
        except Exception as e:
            logger.error(f"Could not load model: {e}")
            return
            
    obs, _ = env.reset()
    terminated = False
    
    total_reward = 0
    details = []
    
    while not terminated:
        action = policy.select_action(obs)
        next_obs, reward, terminated, _, info = env.step(action)
        
        details.append({
            "question": info["question"],
            "action": action.tolist(),
            "reward": reward
        })
        
        total_reward += reward
        obs = next_obs
        
    logger.info(f"Total Evaluation Reward: {total_reward:.2f}")
    
    results = {
        "policy": args.policy,
        "total_reward": total_reward,
        "details": details
    }
    
    os.makedirs("rl/results", exist_ok=True)
    out_path = Path(f"rl/results/{args.policy}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Saved results to {out_path}")

if __name__ == "__main__":
    evaluate()
