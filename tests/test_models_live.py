import os, sys
sys.path.append(os.path.abspath('.'))
import requests
from config.settings import GEMINI_API_KEY, GROQ_API_KEY

print("--- Testing Groq Models ---")
headers = {'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'}
for m in ['qwen/qwen3.6-27b', 'openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'qwen/qwen3.8-27b']:
    try:
        payload = {
            'model': m,
            'messages': [{'role': 'user', 'content': 'Return JSON: {"hello": "world"}'}],
            'response_format': {'type': 'json_object'}
        }
        res = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=payload, timeout=6)
        print(f"Groq {m} -> Status: {res.status_code}, Output: {res.json()['choices'][0]['message']['content'][:40]}")
    except Exception as e:
        print(f"Groq {m} error: {e}")

print("\n--- Testing Gemini Models ---")
for gm in ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-flash-lite-latest', 'gemini-2.5-pro']:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{gm}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": "Hello, return JSON: {\"status\": \"ok\"}"}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=6)
        print(f"Gemini {gm} -> Status: {res.status_code}")
        if res.status_code == 200:
            print("Gemini response:", res.json()['candidates'][0]['content']['parts'][0]['text'][:40])
    except Exception as e:
        print(f"Gemini {gm} error: {e}")
