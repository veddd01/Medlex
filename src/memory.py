"""Conversation memory and rewriting module for the medical chatbot."""
from typing import Dict, List, Any

class ConversationMemory:
    """Stores chat history per session."""
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
    
    def add_interaction(self, session_id: str, question: str, answer: str) -> None:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            
        self.sessions[session_id].append({
            "user": question,
            "bot": answer,
        })
        
        # Trim history if it exceeds max_turns
        if len(self.sessions[session_id]) > self.max_turns:
            self.sessions[session_id] = self.sessions[session_id][-self.max_turns:]
            
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return self.sessions.get(session_id, [])


def rewrite_with_context(question: str, history: List[Dict[str, Any]]) -> str:
    """Rewrite follow-up question using previous context."""
    if not history:
        return question
        
    vague_phrases = [
        "what are its symptoms", "tell me more", "how is it treated", 
        "what is it", "symptoms", "treatment", "its symptoms", "side effects"
    ]
    
    q_lower = question.lower()
    is_vague = any(phrase in q_lower for phrase in vague_phrases) or "its " in q_lower or " it" in q_lower
    
    if is_vague:
        topic = None
        for item in reversed(history):
            if isinstance(item, dict):
                prev_text = item.get("user") or item.get("question") or (item.get("content") if item.get("role") == "user" else "")
                if not prev_text:
                    prev_text = item.get("bot") or item.get("answer") or (item.get("content") if item.get("role") == "assistant" else "")
                
                if prev_text:
                    for prefix in ["what is ", "what are ", "how is ", "how to ", "define "]:
                        if prev_text.lower().startswith(prefix):
                            topic = prev_text[len(prefix):].rstrip("?.,").strip()
                            break
                    if not topic:
                        topic = prev_text.rstrip("?.,").strip()
                    if topic:
                        break
                        
        if topic:
            if "its symptoms" in q_lower:
                return q_lower.replace("its symptoms", f"the symptoms of {topic}").strip()
            elif "its " in q_lower:
                return q_lower.replace("its ", f"{topic}'s ").strip()
            elif " it" in q_lower:
                return q_lower.replace(" it", f" {topic}").strip()
            else:
                return f"{question} (regarding {topic})"
                
    return question


# Global memory instance
memory = ConversationMemory()
