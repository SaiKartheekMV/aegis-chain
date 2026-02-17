import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, endpoint, data=None):
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {name}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        
        print(f"Status: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 201]:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

# Run all tests
print("🚀 Starting Backend Tests...")

tests = [
    ("System Health", "GET", "/", None),
    ("Blockchain Status", "GET", "/blockchain/status", None),
    ("Guardian Policies", "GET", "/guardian/policies", None),
    
    ("AI Parse - Wallet Transfer", "POST", "/ai/parse-intent", {
        "user_intent": "Send 0.01 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    }),
    
    ("AI Parse - Protocol Detection", "POST", "/ai/parse-intent", {
        "user_intent": "Swap 0.02 ETH on Uniswap"
    }),
    
    ("Guardian Validate - Safe TX", "POST", "/guardian/validate", {
        "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "amount": 0.01,
        "ai_confidence": 90,
        "is_protocol_interaction": False
    }),
    
    ("Guardian Validate - Risky TX", "POST", "/guardian/validate", {
        "to_address": "0x1234567890123456789012345678901234567890",
        "amount": 0.5,
        "ai_confidence": 50,
        "is_protocol_interaction": False
    }),
    
    ("Contract Info - EOA", "GET", "/blockchain/contract-info/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", None),
    
    ("Contract Info - Contract", "GET", "/blockchain/contract-info/0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", None),
]

results = []
for test in tests:
    result = test_endpoint(*test)
    results.append(result)

# Summary
print(f"\n{'='*60}")
print("📊 TEST SUMMARY")
print(f"{'='*60}")
print(f"Total: {len(results)}")
print(f"✅ Passed: {sum(results)}")
print(f"❌ Failed: {len(results) - sum(results)}")
print(f"Success Rate: {(sum(results)/len(results))*100:.1f}%")