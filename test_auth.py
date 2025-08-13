import requests
import json

# Test registration
def test_register():
    url = "http://localhost:8000/api/auth/register"
    data = {
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Register Status: {response.status_code}")
        print(f"Register Response: {response.text}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Register Error: {e}")
        return None

# Test login
def test_login():
    url = "http://localhost:8000/api/auth/login"
    data = {
        "email": "test@example.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Login Status: {response.status_code}")
        print(f"Login Response: {response.text}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Login Error: {e}")
        return None

if __name__ == "__main__":
    print("Testing Auth Endpoints...")
    print("\n1. Testing Registration:")
    register_result = test_register()
    
    print("\n2. Testing Login:")
    login_result = test_login()
