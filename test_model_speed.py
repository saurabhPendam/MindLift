import time
import requests

def test_model(model_name):
    """Test model response time"""
    print(f"\n🧪 Testing {model_name}...")
    
    start = time.time()
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": "Hello, how are you?",
                "stream": False,
                "options": {
                    "num_predict": 50,
                    "temperature": 0.7
                }
            },
            timeout=30
        )
        
        end = time.time()
        elapsed = end - start
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            print(f"✅ Response time: {elapsed:.2f}s")
            print(f"📝 Response: {response_text[:100]}...")
            return elapsed
        else:
            print(f"❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("MindLift Model Speed Test")
    print("=" * 50)
    
    # Test each model
    models = ["gemma:2b", "phi3:mini", "phi:latest"]
    results = {}
    
    for model in models:
        time_taken = test_model(model)
        if time_taken:
            results[model] = time_taken
    
    # Show summary
    print("\n" + "=" * 50)
    print("📊 SPEED SUMMARY")
    print("=" * 50)
    
    if results:
        sorted_results = sorted(results.items(), key=lambda x: x[1])
        for model, time_taken in sorted_results:
            print(f"{model:20} → {time_taken:.2f}s")
        
        fastest = sorted_results[0]
        print(f"\n🏆 FASTEST: {fastest[0]} ({fastest[1]:.2f}s)")
    else:
        print("❌ No successful tests")