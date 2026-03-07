import requests, json
from .config import TOKEN_FILE, BASE_URL

def signup():
    username = input("Choose username: ")
    password = input("Choose password: ")

    resp = requests.post(f"{BASE_URL}/auth/signup", json={
        "username": username,
        "password": password
    })

    if resp.status_code != 200:
        print("❌ Signup failed:", resp.text)
        return

    token = resp.json()["access_token"]
    with open(TOKEN_FILE, "w") as f:
        f.write(token)

    print("✅ Signup successful!")

def login():
    username = input("Username: ")
    password = input("Password: ")

    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })

    if resp.status_code != 200:
        print("❌ Login failed:", resp.text)
        return

    token = resp.json()["access_token"]
    with open(TOKEN_FILE, "w") as f:
        f.write(token)

    print("✅ Login successful!")