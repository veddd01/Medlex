import pytest
import json

def test_ask_valid(app_client):
    response = app_client.post('/ask', json={'question': 'What is diabetes?'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'answer' in data
    assert 'sources' in data

def test_ask_missing_question(app_client):
    response = app_client.post('/ask', json={})
    assert response.status_code == 400

def test_ask_empty_question(app_client):
    response = app_client.post('/ask', json={'question': '   '})
    assert response.status_code == 400

def test_ask_too_long(app_client):
    response = app_client.post('/ask', json={'question': 'a' * 1001})
    assert response.status_code == 400

def test_ask_non_json(app_client):
    response = app_client.post('/ask', data='not json')
    assert response.status_code == 400

def test_health(app_client):
    response = app_client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'

def test_root(app_client):
    response = app_client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'service' in data

def test_feedback(app_client):
    response = app_client.post('/feedback', json={
        'question': 'q', 'answer': 'a', 'rating': 'up', 'session_id': '123'
    })
    assert response.status_code == 200

def test_get_history(app_client):
    response = app_client.get('/history/test_session')
    assert response.status_code == 200
    assert 'history' in response.get_json()

def test_ask_emergency(app_client):
    response = app_client.post('/ask', json={'question': 'I am having a heart attack'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['emergency'] is True
    assert '911' in data['answer']

def test_ask_session_memory(app_client):
    response = app_client.post('/ask', json={'question': 'What is diabetes?', 'session_id': 'mem_test'})
    assert response.status_code == 200
    history_resp = app_client.get('/history/mem_test')
    assert len(history_resp.get_json()['history']) > 0
