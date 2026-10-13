"""Baseline policies for RL evaluation."""
import random
import numpy as np
from typing import Dict

class BasePolicy:
    def select_action(self, observation: Dict) -> np.ndarray:
        raise NotImplementedError
        
    def update(self, observation: Dict, action: np.ndarray, reward: float) -> None:
        pass

class FixedPolicy(BasePolicy):
    def select_action(self, observation: Dict) -> np.ndarray:
        # top_k=3 (idx 1), rerank=True (idx 1), min_score=0.3 (idx 1), refuse=False (idx 0)
        return np.array([1, 1, 1, 0])

class RandomPolicy(BasePolicy):
    def __init__(self, action_space):
        self.action_space = action_space
        
    def select_action(self, observation: Dict) -> np.ndarray:
        return self.action_space.sample()

class HeuristicPolicy(BasePolicy):
    def select_action(self, observation: Dict) -> np.ndarray:
        max_score = observation["max_score"][0]
        
        # default
        top_k_idx = 1 # 3
        rerank = 1
        min_score_idx = 1 # 0.3
        refuse = 0
        
        if max_score < 0.3:
            refuse = 1
        elif max_score > 0.7:
            top_k_idx = 0 # 1
            rerank = 0
        else:
            top_k_idx = 1 # 3
            rerank = 1
            
        return np.array([top_k_idx, rerank, min_score_idx, refuse])

class ContextualBanditPolicy(BasePolicy):
    def __init__(self, obs_dim: int, action_dims: list):
        self.obs_dim = obs_dim
        self.action_dims = action_dims
        self.num_actions = int(np.prod(action_dims))
        
        # simple linear weights: action_dim x obs_dim
        self.weights = np.zeros((self.num_actions, self.obs_dim))
        self.epsilon = 1.0
        self.epsilon_decay = 0.99
        self.min_epsilon = 0.1
        self.lr = 0.01
        
    def _flatten_obs(self, obs: Dict) -> np.ndarray:
        features = []
        features.append(obs["question_length"][0])
        
        # one hot question type
        q_type = np.zeros(4)
        q_type[int(obs["question_type"])] = 1.0
        features.extend(q_type)
        
        features.extend(obs["top_similarity_scores"])
        features.append(obs["mean_score"][0])
        features.append(obs["max_score"][0])
        features.append(float(obs["num_chunks_above_threshold"]) / 5.0)
        
        return np.array(features)
        
    def _action_to_idx(self, action: np.ndarray) -> int:
        idx = 0
        multiplier = 1
        for i in range(len(action) - 1, -1, -1):
            idx += action[i] * multiplier
            multiplier *= self.action_dims[i]
        return idx
        
    def _idx_to_action(self, idx: int) -> np.ndarray:
        action = []
        rem = idx
        for i in range(len(self.action_dims) - 1, -1, -1):
            dim = self.action_dims[i]
            action.insert(0, rem % dim)
            rem = rem // dim
        return np.array(action)

    def select_action(self, observation: Dict) -> np.ndarray:
        if random.random() < self.epsilon:
            idx = random.randint(0, self.num_actions - 1)
            return self._idx_to_action(idx)
            
        features = self._flatten_obs(observation)
        q_values = self.weights @ features
        idx = np.argmax(q_values)
        return self._idx_to_action(idx)
        
    def update(self, observation: Dict, action: np.ndarray, reward: float) -> None:
        features = self._flatten_obs(observation)
        idx = self._action_to_idx(action)
        
        # simple Q-learning style update
        prediction = np.dot(self.weights[idx], features)
        error = reward - prediction
        self.weights[idx] += self.lr * error * features
        
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
    def save(self, filepath: str):
        np.savez(filepath, weights=self.weights)
        
    def load(self, filepath: str):
        data = np.load(filepath)
        self.weights = data['weights']
