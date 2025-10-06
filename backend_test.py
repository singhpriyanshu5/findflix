#!/usr/bin/env python3

import asyncio
import httpx
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://tinderflix.preview.emergentagent.com/api"

class FriendRequestTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user1_token = None
        self.user2_token = None
        self.user1_data = None
        self.user2_data = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    async def register_user(self, name: str, email: str, password: str):
        """Register a new user"""
        try:
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json={
                "name": name,
                "email": email,
                "password": password
            })
            
            print(f"Registration response for {email}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User {name} registered successfully")
                return data["session_token"], data["user"]
            else:
                print(f"❌ Registration failed for {email}: {response.text}")
                return None, None
                
        except Exception as e:
            print(f"❌ Registration error for {email}: {str(e)}")
            return None, None
    
    async def send_friend_request(self, sender_token: str, receiver_email: str):
        """Send a friend request"""
        try:
            headers = {"Authorization": f"Bearer {sender_token}"}
            response = await self.client.post(
                f"{BACKEND_URL}/friends/request",
                json={"receiver_email": receiver_email},
                headers=headers
            )
            
            print(f"Friend request response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Friend request sent successfully: {data['message']}")
                return True
            else:
                print(f"❌ Friend request failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Friend request error: {str(e)}")
            return False
    
    async def get_friend_requests(self, user_token: str):
        """Get pending friend requests"""
        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            response = await self.client.get(
                f"{BACKEND_URL}/friends/requests",
                headers=headers
            )
            
            print(f"Get friend requests response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {len(data)} friend requests")
                return data
            else:
                print(f"❌ Get friend requests failed: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Get friend requests error: {str(e)}")
            return []
    
    async def run_focused_test(self):
        """Run the focused friend request test"""
        print("=" * 60)
        print("FOCUSED FRIEND REQUEST TEST WITH ENHANCED LOGGING")
        print("=" * 60)
        
        # Generate unique emails with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user1_email = f"alice_{timestamp}@test.com"
        user2_email = f"bob_{timestamp}@test.com"
        
        print(f"\n1. Creating test users:")
        print(f"   User 1: Alice ({user1_email})")
        print(f"   User 2: Bob ({user2_email})")
        
        # Step 1: Create 2 test users
        self.user1_token, self.user1_data = await self.register_user(
            "Alice", user1_email, "password123"
        )
        
        self.user2_token, self.user2_data = await self.register_user(
            "Bob", user2_email, "password123"
        )
        
        if not self.user1_token or not self.user2_token:
            print("❌ Failed to create test users")
            return False
        
        print(f"\n2. Sending friend request from Alice to Bob...")
        
        # Step 2: Send friend request from user 1 to user 2
        success = await self.send_friend_request(self.user1_token, user2_email)
        
        if not success:
            print("❌ Failed to send friend request")
            return False
        
        print(f"\n3. Checking friend requests for Bob...")
        
        # Step 3: Check friend requests for user 2
        requests = await self.get_friend_requests(self.user2_token)
        
        # Analyze results
        print(f"\n" + "=" * 60)
        print("TEST RESULTS:")
        print("=" * 60)
        
        if len(requests) > 0:
            print(f"✅ SUCCESS: Bob received {len(requests)} friend request(s)")
            for req in requests:
                print(f"   - Request ID: {req['id']}")
                print(f"   - From: {req['sender']['name']} ({req['sender']['email']})")
                print(f"   - Status: {req['status']}")
                print(f"   - Created: {req['created_at']}")
            return True
        else:
            print(f"❌ FAILURE: Bob received 0 friend requests")
            print("   This indicates the friend request system is still not working properly")
            return False

async def main():
    """Main test function"""
    tester = FriendRequestTester()
    
    try:
        success = await tester.run_focused_test()
        
        print(f"\n" + "=" * 60)
        print("LOGGING ANALYSIS:")
        print("=" * 60)
        print("Check the backend logs for the following enhanced logging messages:")
        print("- 'Creating friend request: {data}'")
        print("- 'Friend request created with ID: {id}'") 
        print("- 'Verification query result: {result}'")
        print("- 'Looking for friend requests for user: {user_id}'")
        print("- 'Found X pending requests for user {user_id}'")
        
        if success:
            print(f"\n🎉 FRIEND REQUEST SYSTEM IS WORKING!")
            return 0
        else:
            print(f"\n💥 FRIEND REQUEST SYSTEM STILL HAS ISSUES!")
            return 1
            
    except Exception as e:
        print(f"❌ Test execution error: {str(e)}")
        return 1
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)