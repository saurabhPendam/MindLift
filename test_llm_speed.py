import time
import requests

def test_ollama_speed():
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "mindlift",
        "prompt": "I'm feeling anxious",
        "stream": False,
        "options": {
            "temperature": 0.5,
            "num_predict": 120
        }
    }

    start = time.time()
    response = requests.post(url, json=payload, timeout=60)
    end = time.time()

    data = response.json()

    print(f"Response time: {end - start:.2f} seconds")
    print("Response:", data["response"])

if __name__ == "__main__":
    test_ollama_speed()
