from src.memory import ConversationMemory, rewrite_with_context

def test_memory_add_get():
    mem = ConversationMemory(max_turns=2)
    mem.add_interaction("s1", "q1", "a1")
    history = mem.get_history("s1")
    assert len(history) == 1
    assert history[0] == {"user": "q1", "bot": "a1"}

def test_memory_max_turns():
    mem = ConversationMemory(max_turns=2)
    mem.add_interaction("s1", "q1", "a1")
    mem.add_interaction("s1", "q2", "a2")
    mem.add_interaction("s1", "q3", "a3")
    history = mem.get_history("s1")
    assert len(history) == 2
    assert history[0]["user"] == "q2"
    assert history[1]["user"] == "q3"

def test_rewrite_with_context():
    history = [{"user": "What is diabetes?", "bot": "It is a disease."}]
    rewritten = rewrite_with_context("What are its symptoms?", history)
    assert "diabetes" in rewritten.lower()
