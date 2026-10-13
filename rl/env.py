"""Gymnasium-style RL environment for optimizing RAG retrieval settings.

The agent observes features of the incoming question and the retrieval
results, then chooses actions (top_k, whether to rerank, min_score
threshold, whether to refuse). The reward is computed from the Phase 2
evaluation set (correct page retrieved, grounded answer, correct refusal).

This is an experiment on retrieval settings, not a claim that the chatbot
is "trained with RL".
"""
import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from src.emergency import check_emergency

logger = logging.getLogger(__name__)

class MockRetriever:
    """Mock retriever that generates results based on eval questions."""
    def __init__(self, eval_data: List[Dict]):
        self.eval_data = eval_data
        self.question_to_data = {q['question']: q for q in eval_data}
        
    def retrieve(self, question: str, top_k: int) -> List[Dict]:
        data = self.question_to_data.get(question)
        if not data:
            return []
            
        chunks = []
        # If expected_pages exists, generate high-scoring chunks for them
        expected_pages = data.get('expected_pages', [])
        
        for i, page in enumerate(expected_pages):
            score = 0.95 - (i * 0.05)
            chunks.append({
                "page": page,
                "text": f"Mock text for page {page} with keywords: {', '.join(data.get('expected_keywords', []))}",
                "score": score
            })
            
        # Add distractors
        num_distractors = 5 - len(chunks)
        for i in range(num_distractors):
            score = 0.5 - (i * 0.1)
            chunks.append({
                "page": 999 + i,
                "text": "Distractor mock text.",
                "score": max(0.1, score)
            })
            
        # If unanswerable, only keep distractors (or lower scores)
        if not data.get('answerable', True):
            for c in chunks:
                c['score'] = c['score'] * 0.5
                c['page'] = 999 + random.randint(0, 100)
                
        # Sort by score desc and return top_k
        chunks.sort(key=lambda x: x['score'], reverse=True)
        return chunks[:top_k]

class RAGOptimizationEnv(gym.Env):
    """Gymnasium-style RL environment for optimizing RAG retrieval settings."""
    
    def __init__(self, eval_file: str, use_mock: bool = True):
        super().__init__()
        
        # Load eval data
        with open(eval_file, "r") as f:
            self.eval_data = json.load(f)
            
        self.use_mock = use_mock
        if use_mock:
            self.retriever = MockRetriever(self.eval_data)
        else:
            # We would initialize a real retriever here
            raise NotImplementedError("Real retriever not implemented for env")
            
        self.current_step = 0
        self.current_question = None
        
        # Observation space
        self.observation_space = spaces.Dict({
            "question_length": spaces.Box(low=0, high=1, shape=(1,)),
            "question_type": spaces.Discrete(4),
            "top_similarity_scores": spaces.Box(low=0, high=1, shape=(5,)),
            "mean_score": spaces.Box(low=0, high=1, shape=(1,)),
            "max_score": spaces.Box(low=0, high=1, shape=(1,)),
            "num_chunks_above_threshold": spaces.Discrete(6)
        })
        
        # Action space
        # top_k_choice: 3 options (1, 3, 5)
        # rerank: 2 options (no, yes)
        # min_score_choice: 3 options (0.2, 0.3, 0.5)
        # refuse: 2 options (answer, refuse)
        self.action_space = spaces.MultiDiscrete([3, 2, 3, 2])
        
        self.top_k_mapping = [1, 3, 5]
        self.min_score_mapping = [0.2, 0.3, 0.5]
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        return self._get_obs(self.eval_data[self.current_step]), {}
        
    def _classify_question(self, q: str) -> int:
        q_lower = q.lower()
        if q_lower.startswith('what is') or q_lower.startswith('define'):
            return 2 # definitional
        elif q_lower.startswith('how to') or q_lower.startswith('how do'):
            return 1 # procedural
        elif q_lower.startswith('is there') or q_lower.startswith('what are'):
            return 0 # factual
        return 3 # other
        
    def _get_obs(self, data: Dict) -> Dict:
        q = data['question']
        
        # question length normalized (assume max 200 chars)
        q_len = min(1.0, len(q) / 200.0)
        
        q_type = self._classify_question(q)
        
        # Run an initial retrieval with max top_k (5) to get score stats
        chunks = self.retriever.retrieve(q, 5)
        scores = [c['score'] for c in chunks]
        
        padded_scores = scores + [0.0] * (5 - len(scores))
        
        mean_score = np.mean(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        # use 0.3 as a baseline threshold for observation
        num_above = sum(1 for s in scores if s > 0.3)
        
        return {
            "question_length": np.array([q_len], dtype=np.float32),
            "question_type": q_type,
            "top_similarity_scores": np.array(padded_scores[:5], dtype=np.float32),
            "mean_score": np.array([mean_score], dtype=np.float32),
            "max_score": np.array([max_score], dtype=np.float32),
            "num_chunks_above_threshold": num_above
        }
        
    def step(self, action):
        data = self.eval_data[self.current_step]
        q = data['question']
        
        # SAFETY RULE: check emergency before anything
        emergency_msg = check_emergency(q)
        if emergency_msg:
            # Auto-refuse
            refuse = 1
        else:
            top_k_idx, rerank, min_score_idx, refuse = action
            top_k = self.top_k_mapping[top_k_idx]
            min_score = self.min_score_mapping[min_score_idx]
            
        # compute reward
        reward = 0.0
        
        if refuse == 1:
            if not data.get('answerable', True):
                reward += 1.0 # correctly refused
            else:
                reward -= 0.5 # incorrectly refused
        else:
            # answered
            if not data.get('answerable', True):
                reward -= 1.0 # incorrectly answered
            else:
                chunks = self.retriever.retrieve(q, top_k)
                # apply min_score
                chunks = [c for c in chunks if c['score'] >= min_score]
                
                retrieved_pages = [c['page'] for c in chunks]
                expected_pages = data.get('expected_pages', [])
                
                # +1.0 if an expected page was in retrieved sources
                if expected_pages and any(p in retrieved_pages for p in expected_pages):
                    reward += 1.0
                    
                # Mock keyword coverage
                expected_kw = data.get('expected_keywords', [])
                if expected_kw:
                    # In a real environment, we'd check the generated answer.
                    # Here we simulate keyword coverage based on the retrieved chunks
                    chunk_texts = " ".join([c['text'].lower() for c in chunks])
                    hits = sum(1 for kw in expected_kw if kw.lower() in chunk_texts)
                    coverage = hits / len(expected_kw)
                    reward += 0.5 * coverage
                    
                reward -= 0.1 * len(chunks) # efficiency penalty
                
        self.current_step += 1
        terminated = self.current_step >= len(self.eval_data)
        truncated = False
        
        obs = self._get_obs(self.eval_data[self.current_step]) if not terminated else self._get_obs(self.eval_data[0])
        
        info = {
            "question": q,
            "action": action,
            "reward": reward
        }
        
        return obs, reward, terminated, truncated, info
