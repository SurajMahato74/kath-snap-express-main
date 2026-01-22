#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://ezeyway.com"
RECEIVER_TOKEN = "145e8af3804176faf14e17200bb13cb6028ad032"  # User 2 token
CALL_ID = "call_79_2_1769110843"  # From previous test

print("🔍 Testing CORRECT accept endpoint...")

# Test the correct endpoint
accept_response = requests.post(
    f"{BASE_URL}/api/calls/{CALL_ID}/accept/",
    headers={
        "Authorization": f"Token {RECEIVER_TOKEN}",
        "Content-Type": "application/json"
    },
    json={}
)

print(f"Accept status: {accept_response.status_code}")
print(f"Accept response: {accept_response.text}")

if accept_response.status_code == 200:
    response_data = accept_response.json()
    if "agora_token" in response_data:
        print(f"✅ Agora token included: {response_data['agora_token'][:30]}...")
    else:
        print("❌ No Agora token in response!")