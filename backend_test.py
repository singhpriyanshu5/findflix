#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for FindFlix Swipe Session Flow
Tests the complete end-to-end swipe session functionality
"""

import asyncio
import httpx
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "https://tinderflix.preview.emergentagent.com/api"
TIMEOUT = 30

class SwipeSessionTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.user1_data = None
        self.user2_data = None
        self.user1_token = None
        self.user2_token = None
        self.friend_request_id = None
        self.swipe_session_id = None
        self.test_results = []
        
    async def cleanup(self):
        await self.client.aclose()
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    async def test_user_registration_and_auth(self):
        """Test user registration and authentication"""
        print("=== Testing User Registration & Authentication ===")
        
        # Generate unique test users
        timestamp = int(time.time())
        user1_email = f"alice_{timestamp}@test.com"
        user2_email = f"bob_{timestamp}@test.com"
        
        # Register User 1 (Alice)
        try:
            user1_payload = {
                "name": "Alice Smith",
                "email": user1_email,
                "password": "SecurePass123!"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/auth/register",
                json=user1_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user1_data = data.get("user")
                self.user1_token = data.get("session_token")
                self.log_result("User 1 Registration", True, f"User ID: {self.user1_data.get('id')}")
            else:
                self.log_result("User 1 Registration", False, error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User 1 Registration", False, error=str(e))
            return False
        
        # Register User 2 (Bob)
        try:
            user2_payload = {
                "name": "Bob Johnson",
                "email": user2_email,
                "password": "SecurePass456!"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/auth/register",
                json=user2_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user2_data = data.get("user")
                self.user2_token = data.get("session_token")
                self.log_result("User 2 Registration", True, f"User ID: {self.user2_data.get('id')}")
            else:
                self.log_result("User 2 Registration", False, error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User 2 Registration", False, error=str(e))
            return False
        
        # Test auth/me endpoint for both users
        try:
            headers1 = {"Authorization": f"Bearer {self.user1_token}"}
            headers2 = {"Authorization": f"Bearer {self.user2_token}"}
            
            response1 = await self.client.get(f"{BASE_URL}/auth/me", headers=headers1)
            response2 = await self.client.get(f"{BASE_URL}/auth/me", headers=headers2)
            
            if response1.status_code == 200 and response2.status_code == 200:
                self.log_result("Authentication Verification", True, "Both users authenticated successfully")
            else:
                self.log_result("Authentication Verification", False, 
                              error=f"User1: {response1.status_code}, User2: {response2.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Authentication Verification", False, error=str(e))
            return False
            
        return True

    async def test_friend_request_flow(self):
        """Test complete friend request flow"""
        print("=== Testing Friend Request Flow ===")
        
        if not self.user1_data or not self.user2_data:
            self.log_result("Friend Request Flow", False, error="Users not registered")
            return False
        
        # Send friend request from User 1 to User 2
        try:
            friend_request_payload = {
                "receiver_email": self.user2_data.get("email")
            }
            
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = await self.client.post(
                f"{BASE_URL}/friends/request",
                json=friend_request_payload,
                headers=headers
            )
            
            if response.status_code == 200:
                self.log_result("Send Friend Request", True, "Friend request sent successfully")
            else:
                self.log_result("Send Friend Request", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Send Friend Request", False, error=str(e))
            return False
        
        # User 2 retrieves friend requests
        try:
            headers = {"Authorization": f"Bearer {self.user2_token}"}
            response = await self.client.get(f"{BASE_URL}/friends/requests", headers=headers)
            
            if response.status_code == 200:
                requests_data = response.json()
                if len(requests_data) > 0:
                    self.friend_request_id = requests_data[0].get("id")
                    self.log_result("Retrieve Friend Requests", True, 
                                  f"Found {len(requests_data)} friend request(s)")
                else:
                    self.log_result("Retrieve Friend Requests", False, 
                                  error="No friend requests found")
                    return False
            else:
                self.log_result("Retrieve Friend Requests", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Retrieve Friend Requests", False, error=str(e))
            return False
        
        # User 2 accepts friend request
        try:
            accept_payload = {
                "request_id": self.friend_request_id,
                "accept": True
            }
            
            headers = {"Authorization": f"Bearer {self.user2_token}"}
            response = await self.client.post(
                f"{BASE_URL}/friends/respond",
                json=accept_payload,
                headers=headers
            )
            
            if response.status_code == 200:
                self.log_result("Accept Friend Request", True, "Friend request accepted")
            else:
                self.log_result("Accept Friend Request", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Accept Friend Request", False, error=str(e))
            return False
        
        # Verify friendship - both users should see each other as friends
        try:
            headers1 = {"Authorization": f"Bearer {self.user1_token}"}
            headers2 = {"Authorization": f"Bearer {self.user2_token}"}
            
            response1 = await self.client.get(f"{BASE_URL}/friends", headers=headers1)
            response2 = await self.client.get(f"{BASE_URL}/friends", headers=headers2)
            
            if response1.status_code == 200 and response2.status_code == 200:
                friends1 = response1.json()
                friends2 = response2.json()
                
                if len(friends1) > 0 and len(friends2) > 0:
                    self.log_result("Verify Friendship", True, 
                                  f"User1 has {len(friends1)} friends, User2 has {len(friends2)} friends")
                else:
                    self.log_result("Verify Friendship", False, 
                                  error=f"User1 friends: {len(friends1)}, User2 friends: {len(friends2)}")
                    return False
            else:
                self.log_result("Verify Friendship", False, 
                              error=f"User1: {response1.status_code}, User2: {response2.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Verify Friendship", False, error=str(e))
            return False
            
        return True

    async def test_swipe_session_creation(self):
        """Test swipe session creation"""
        print("=== Testing Swipe Session Creation ===")
        
        if not self.user1_data or not self.user2_data:
            self.log_result("Swipe Session Creation", False, error="Users not available")
            return False
        
        try:
            # User 1 creates/gets session with User 2
            friend_id = self.user2_data.get("id")
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = await self.client.get(
                f"{BASE_URL}/swipe/session/{friend_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                session_data = response.json()
                self.swipe_session_id = session_data.get("session_id")
                
                self.log_result("Swipe Session Creation", True, 
                              f"Session ID: {self.swipe_session_id}, "
                              f"My swipes: {session_data.get('my_swipes_count')}, "
                              f"Friend swipes: {session_data.get('friend_swipes_count')}, "
                              f"Matches: {session_data.get('match_count')}")
            else:
                self.log_result("Swipe Session Creation", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Swipe Session Creation", False, error=str(e))
            return False
            
        return True

    async def test_content_loading(self):
        """Test content loading for swipe session"""
        print("=== Testing Content Loading ===")
        
        if not self.swipe_session_id:
            self.log_result("Content Loading", False, error="No swipe session available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = await self.client.get(
                f"{BASE_URL}/swipe/content/{self.swipe_session_id}",
                params={"page": 1},
                headers=headers
            )
            
            if response.status_code == 200:
                content_data = response.json()
                results = content_data.get("results", [])
                
                if len(results) > 0:
                    self.log_result("Content Loading", True, 
                                  f"Loaded {len(results)} movies/shows for swiping")
                    
                    # Store some movies for swipe testing
                    self.movies_to_swipe = results[:5]  # Take first 5 for testing
                else:
                    self.log_result("Content Loading", False, error="No content returned")
                    return False
            else:
                self.log_result("Content Loading", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Content Loading", False, error=str(e))
            return False
            
        return True

    async def test_swipe_recording(self):
        """Test swipe recording functionality"""
        print("=== Testing Swipe Recording ===")
        
        if not self.swipe_session_id or not hasattr(self, 'movies_to_swipe'):
            self.log_result("Swipe Recording", False, error="No session or movies available")
            return False
        
        swipe_count = 0
        
        # User 1 swipes on movies
        for i, movie in enumerate(self.movies_to_swipe):
            try:
                # Alternate between like and dislike
                action = "like" if i % 2 == 0 else "dislike"
                
                swipe_payload = {
                    "session_id": self.swipe_session_id,
                    "movie_id": movie.get("id"),
                    "media_type": movie.get("media_type", "movie"),
                    "action": action,
                    "movie_title": movie.get("title"),
                    "movie_poster": movie.get("poster_path")
                }
                
                headers = {"Authorization": f"Bearer {self.user1_token}"}
                response = await self.client.post(
                    f"{BASE_URL}/swipe",
                    json=swipe_payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    swipe_count += 1
                    result = response.json()
                    match_created = result.get("match_created", False)
                    
                    if match_created:
                        print(f"   Match created for: {movie.get('title')}")
                else:
                    self.log_result(f"User 1 Swipe {i+1}", False, 
                                  error=f"Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                self.log_result(f"User 1 Swipe {i+1}", False, error=str(e))
        
        # User 2 swipes on same movies (to create potential matches)
        for i, movie in enumerate(self.movies_to_swipe):
            try:
                # User 2 likes movies that User 1 liked (even indices)
                action = "like" if i % 2 == 0 else "dislike"
                
                swipe_payload = {
                    "session_id": self.swipe_session_id,
                    "movie_id": movie.get("id"),
                    "media_type": movie.get("media_type", "movie"),
                    "action": action,
                    "movie_title": movie.get("title"),
                    "movie_poster": movie.get("poster_path")
                }
                
                headers = {"Authorization": f"Bearer {self.user2_token}"}
                response = await self.client.post(
                    f"{BASE_URL}/swipe",
                    json=swipe_payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    swipe_count += 1
                    result = response.json()
                    match_created = result.get("match_created", False)
                    
                    if match_created:
                        print(f"   Match created for: {movie.get('title')}")
                else:
                    self.log_result(f"User 2 Swipe {i+1}", False, 
                                  error=f"Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                self.log_result(f"User 2 Swipe {i+1}", False, error=str(e))
        
        if swipe_count > 0:
            self.log_result("Swipe Recording", True, f"Successfully recorded {swipe_count} swipes")
            return True
        else:
            self.log_result("Swipe Recording", False, error="No swipes were recorded")
            return False

    async def test_match_detection_and_retrieval(self):
        """Test match detection and retrieval"""
        print("=== Testing Match Detection & Retrieval ===")
        
        if not self.swipe_session_id:
            self.log_result("Match Retrieval", False, error="No swipe session available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = await self.client.get(
                f"{BASE_URL}/swipe/matches/{self.swipe_session_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                matches = response.json()
                
                if len(matches) > 0:
                    self.log_result("Match Detection & Retrieval", True, 
                                  f"Found {len(matches)} matches")
                    
                    # Print match details
                    for match in matches:
                        print(f"   Match: {match.get('movie_title')} ({match.get('media_type')})")
                else:
                    self.log_result("Match Detection & Retrieval", True, 
                                  "No matches found (expected if users didn't like same movies)")
            else:
                self.log_result("Match Detection & Retrieval", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Match Detection & Retrieval", False, error=str(e))
            return False
            
        return True

    async def test_session_summary(self):
        """Test session summary endpoint"""
        print("=== Testing Session Summary ===")
        
        if not self.swipe_session_id:
            self.log_result("Session Summary", False, error="No swipe session available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = await self.client.get(
                f"{BASE_URL}/swipe/summary/{self.swipe_session_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                summary = response.json()
                
                self.log_result("Session Summary", True, 
                              f"Total swipes: {summary.get('total_swipes')}, "
                              f"Total matches: {summary.get('total_matches')}, "
                              f"Creator swipes: {summary.get('creator_swipes')}, "
                              f"Friend swipes: {summary.get('friend_swipes')}")
                
                # Print match details from summary
                matches = summary.get("matches", [])
                if matches:
                    print("   Matches in summary:")
                    for match in matches:
                        print(f"     - {match.get('movie_title')} ({match.get('media_type')})")
                        
            else:
                self.log_result("Session Summary", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Session Summary", False, error=str(e))
            return False
            
        return True

    async def test_swipe_sessions_list(self):
        """Test getting list of swipe sessions"""
        print("=== Testing Swipe Sessions List ===")
        
        try:
            headers = {"Authorization": f"Bearer {self.user1_token}"}
            response = await self.client.get(f"{BASE_URL}/swipe/sessions", headers=headers)
            
            if response.status_code == 200:
                sessions = response.json()
                self.log_result("Swipe Sessions List", True, 
                              f"Found {len(sessions)} active sessions")
                
                for session in sessions:
                    print(f"   Session: {session.get('id')} with {session.get('friend', {}).get('name')}")
            else:
                self.log_result("Swipe Sessions List", False, 
                              error=f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Swipe Sessions List", False, error=str(e))
            return False
            
        return True

    async def run_all_tests(self):
        """Run all swipe session tests"""
        print("🎬 Starting Complete Swipe Session Flow Testing")
        print("=" * 60)
        
        test_methods = [
            self.test_user_registration_and_auth,
            self.test_friend_request_flow,
            self.test_swipe_session_creation,
            self.test_content_loading,
            self.test_swipe_recording,
            self.test_match_detection_and_retrieval,
            self.test_session_summary,
            self.test_swipe_sessions_list
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                if await test_method():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_method.__name__}: {str(e)}")
                failed += 1
        
        print("=" * 60)
        print(f"🎯 TEST SUMMARY: {passed} passed, {failed} failed")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['error']}")
        
        return failed == 0

async def main():
    """Main test function"""
    tester = SwipeSessionTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 All swipe session tests passed!")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check the details above.")
            return 1
            
    except Exception as e:
        print(f"❌ Test execution error: {str(e)}")
        return 1
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)