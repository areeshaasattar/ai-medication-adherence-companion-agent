import asyncio
import httpx
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000/api/v1"

async def test_auth_flow():
    print("--- Starting Auth Flow Test ---")
    
    email = f"test_{os.urandom(4).hex()}@example.com"
    password = "StrongPassword123!"
    
    async with httpx.AsyncClient() as client:
        # 1. Register
        print(f"\n1. Registering user: {email}")
        reg_resp = await client.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Test User"
        })
        print(f"Status: {reg_resp.status_code}")
        if reg_resp.status_code != 201:
            print(f"Error: {reg_resp.text}")
            return

        # 2. Login
        print("\n2. Logging in...")
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        print(f"Status: {login_resp.status_code}")
        if login_resp.status_code != 200:
            print(f"Error: {login_resp.text}")
            return
        
        tokens = login_resp.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        print("Tokens received successfully.")

        # 3. Get Me
        print("\n3. Testing /auth/me with access token...")
        headers = {"Authorization": f"Bearer {access_token}"}
        me_resp = await client.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Status: {me_resp.status_code}")
        if me_resp.status_code == 200:
            print(f"Me Data: {me_resp.json()}")

        # 4. Refresh Token
        print("\n4. Testing /auth/refresh...")
        refresh_resp = await client.post(f"{BASE_URL}/auth/refresh", json={
            "refresh_token": refresh_token
        })
        print(f"Status: {refresh_resp.status_code}")
        if refresh_resp.status_code == 200:
            new_tokens = refresh_resp.json()
            print("Access token refreshed successfully.")
            access_token = new_tokens["access_token"]

        # 5. Logout
        print("\n5. Logging out...")
        logout_resp = await client.post(f"{BASE_URL}/auth/logout", json={
            "refresh_token": refresh_token
        })
        print(f"Status: {logout_resp.status_code}")
        if logout_resp.status_code == 204:
            print("Logged out successfully.")

if __name__ == "__main__":
    print("Note: Ensure the FastAPI server is running before executing this test.")
    # asyncio.run(test_auth_flow())
