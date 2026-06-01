import urllib.request
import json
import sys

def test():
    url = "http://localhost:8002/api/v2/chat"
    data = {
        "query": "Assign \"VIEW_DASHBOARD\" permission to \"Sales\" role",
        "history": []
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    print("Sending live test request to chat API...")
    try:
        with urllib.request.urlopen(req) as response:
            for line in response:
                line_str = line.decode('utf-8').strip()
                if line_str.startswith("data: "):
                    payload = json.loads(line_str[6:])
                    t = payload.get("type")
                    if t == "log":
                        print(f"[Live Server] {payload.get('content')}")
                    elif t == "result":
                        print("\n[Result Payload]")
                        print(json.dumps(payload.get("payload"), indent=2))
                    elif t == "error":
                        print(f"\n[Server Error] {payload.get('error')}")
    except Exception as e:
        print(f"Failed to communicate with API: {e}")

if __name__ == "__main__":
    test()
