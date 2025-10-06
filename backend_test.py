#!/usr/bin/env python3
"""
Backend API Testing for FindFlix API with Tinder Functionality
Tests all endpoints including new authentication and friend system
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://tinderflix.preview.emergentagent.com/api"

class FindFlixAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.user_data = None
        self.friend_user_data = None
        self.friend_auth_token = None
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def test_health_check(self):
        """Test GET /api/ - Health check with Tinder feature message"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "status" in data:
                    # Check for Tinder feature message
                    if "Tinder" in data["message"]:
                        self.log_test("Health Check", True, f"API is running with Tinder feature: {data['message']}")
                        return True
                    else:
                        self.log_test("Health Check", True, f"API is running: {data['message']}")
                        return True
                else:
                    self.log_test("Health Check", False, "Invalid response format")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False

    # ===== Authentication Tests =====
    
    def test_user_registration(self):
        """Test POST /api/auth/register - User registration"""
        try:
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            payload = {
                "name": "Emma Watson",
                "email": f"emma.watson.{unique_id}@findflix.com",
                "password": "SecurePass123!"
            }
            response = self.session.post(f"{self.base_url}/auth/register", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "user" in data and "session_token" in data:
                    self.user_data = data["user"]
                    self.auth_token = data["session_token"]
                    self.log_test("User Registration", True, f"User registered: {data['user']['name']} ({data['user']['email']})")
                    return True
                else:
                    self.log_test("User Registration", False, "Invalid response format")
                    return False
            else:
                self.log_test("User Registration", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("User Registration", False, f"Error: {str(e)}")
            return False

    def test_user_login(self):
        """Test POST /api/auth/login - User login"""
        try:
            # Use the email from registration
            if not self.user_data:
                self.log_test("User Login", False, "No user data from registration")
                return False
                
            payload = {
                "email": self.user_data["email"],
                "password": "SecurePass123!"
            }
            response = self.session.post(f"{self.base_url}/auth/login", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "user" in data and "session_token" in data:
                    # Update auth token from login
                    self.auth_token = data["session_token"]
                    self.log_test("User Login", True, f"User logged in: {data['user']['name']}")
                    return True
                else:
                    self.log_test("User Login", False, "Invalid response format")
                    return False
            else:
                self.log_test("User Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("User Login", False, f"Error: {str(e)}")
            return False

    def test_get_current_user(self):
        """Test GET /api/auth/me - Get current user profile"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and "name" in data and "email" in data:
                    self.log_test("Get Current User", True, f"Retrieved user profile: {data['name']} ({data['email']})")
                    return True
                else:
                    self.log_test("Get Current User", False, "Invalid response format")
                    return False
            elif response.status_code == 401:
                self.log_test("Get Current User", False, "Authentication required (expected if no token)")
                return False
            else:
                self.log_test("Get Current User", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Current User", False, f"Error: {str(e)}")
            return False

    def test_friend_user_registration(self):
        """Test registering a second user for friend system testing"""
        try:
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            payload = {
                "name": "Ryan Gosling",
                "email": f"ryan.gosling.{unique_id}@findflix.com",
                "password": "AnotherSecurePass456!"
            }
            response = self.session.post(f"{self.base_url}/auth/register", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "user" in data and "session_token" in data:
                    self.friend_user_data = data["user"]
                    self.friend_auth_token = data["session_token"]
                    self.log_test("Friend User Registration", True, f"Friend user registered: {data['user']['name']}")
                    return True
                else:
                    self.log_test("Friend User Registration", False, "Invalid response format")
                    return False
            else:
                self.log_test("Friend User Registration", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Friend User Registration", False, f"Error: {str(e)}")
            return False

    # ===== Friend System Tests =====

    def test_send_friend_request(self):
        """Test POST /api/friends/request - Send friend request"""
        try:
            if not self.auth_token or not self.friend_user_data:
                self.log_test("Send Friend Request", False, "Missing authentication or friend user data")
                return False
                
            payload = {
                "receiver_email": self.friend_user_data["email"]
            }
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.post(f"{self.base_url}/friends/request", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Send Friend Request", True, f"Friend request sent: {data['message']}")
                    return True
                else:
                    self.log_test("Send Friend Request", False, "Invalid response format")
                    return False
            else:
                self.log_test("Send Friend Request", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Send Friend Request", False, f"Error: {str(e)}")
            return False

    def test_get_friend_requests(self):
        """Test GET /api/friends/requests - Get pending friend requests"""
        try:
            if not self.friend_auth_token:
                self.log_test("Get Friend Requests", False, "Missing friend authentication token")
                return False
                
            headers = {"Authorization": f"Bearer {self.friend_auth_token}"}
            response = self.session.get(f"{self.base_url}/friends/requests", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    if len(data) > 0:
                        # Store the request ID for responding
                        self.friend_request_id = data[0]["id"]
                        self.log_test("Get Friend Requests", True, f"Found {len(data)} pending friend requests")
                        return True
                    else:
                        self.log_test("Get Friend Requests", True, "No pending friend requests found")
                        return True
                else:
                    self.log_test("Get Friend Requests", False, "Invalid response format")
                    return False
            else:
                self.log_test("Get Friend Requests", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Friend Requests", False, f"Error: {str(e)}")
            return False

    def test_accept_friend_request(self):
        """Test POST /api/friends/respond - Accept friend request"""
        try:
            if not self.friend_auth_token or not hasattr(self, 'friend_request_id'):
                self.log_test("Accept Friend Request", False, "Missing friend auth token or request ID")
                return False
                
            payload = {
                "request_id": self.friend_request_id,
                "accept": True
            }
            headers = {"Authorization": f"Bearer {self.friend_auth_token}"}
            response = self.session.post(f"{self.base_url}/friends/respond", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Accept Friend Request", True, f"Friend request accepted: {data['message']}")
                    return True
                else:
                    self.log_test("Accept Friend Request", False, "Invalid response format")
                    return False
            else:
                self.log_test("Accept Friend Request", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Accept Friend Request", False, f"Error: {str(e)}")
            return False

    def test_get_friends_list(self):
        """Test GET /api/friends - Get friends list"""
        try:
            if not self.auth_token:
                self.log_test("Get Friends List", False, "Missing authentication token")
                return False
                
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{self.base_url}/friends", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Friends List", True, f"Retrieved {len(data)} friends")
                    return True
                else:
                    self.log_test("Get Friends List", False, "Invalid response format")
                    return False
            else:
                self.log_test("Get Friends List", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Friends List", False, f"Error: {str(e)}")
            return False

    def test_logout(self):
        """Test POST /api/auth/logout - User logout"""
        try:
            if not self.auth_token:
                self.log_test("User Logout", False, "Missing authentication token")
                return False
                
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.post(f"{self.base_url}/auth/logout", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("User Logout", True, f"User logged out: {data['message']}")
                    return True
                else:
                    self.log_test("User Logout", False, "Invalid response format")
                    return False
            else:
                self.log_test("User Logout", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("User Logout", False, f"Error: {str(e)}")
            return False

    # ===== Swipe Session Tests =====

    def test_create_swipe_session(self):
        """Test GET /api/swipe/session/{friend_id} - Create/get swipe session"""
        try:
            if not self.auth_token or not self.friend_user_data:
                self.log_test("Create Swipe Session", False, "Missing authentication or friend user data")
                return False
                
            friend_id = self.friend_user_data["id"]
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{self.base_url}/swipe/session/{friend_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "session_id" in data:
                    self.swipe_session_id = data["session_id"]
                    self.log_test("Create Swipe Session", True, 
                                f"Session created/retrieved: {data['session_id']}, My swipes: {data.get('my_swipes_count', 0)}, Friend swipes: {data.get('friend_swipes_count', 0)}")
                    return True
                else:
                    self.log_test("Create Swipe Session", False, "Invalid response format")
                    return False
            else:
                self.log_test("Create Swipe Session", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create Swipe Session", False, f"Error: {str(e)}")
            return False

    def test_get_swipe_content(self):
        """Test GET /api/swipe/content/{session_id} - Get content for swiping"""
        try:
            if not self.auth_token or not hasattr(self, 'swipe_session_id'):
                self.log_test("Get Swipe Content", False, "Missing authentication or session ID")
                return False
                
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{self.base_url}/swipe/content/{self.swipe_session_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data and len(data["results"]) > 0:
                    # Store first movie for swipe testing
                    self.test_movie = data["results"][0]
                    self.log_test("Get Swipe Content", True, 
                                f"Retrieved {len(data['results'])} movies for swiping")
                    return True
                else:
                    self.log_test("Get Swipe Content", False, "No content available for swiping")
                    return False
            else:
                self.log_test("Get Swipe Content", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Swipe Content", False, f"Error: {str(e)}")
            return False

    def test_submit_swipe_like(self):
        """Test POST /api/swipe - Submit a like swipe"""
        try:
            if not self.auth_token or not hasattr(self, 'test_movie') or not hasattr(self, 'swipe_session_id'):
                self.log_test("Submit Swipe (Like)", False, "Missing authentication, session ID, or test movie")
                return False
                
            payload = {
                "session_id": self.swipe_session_id,
                "movie_id": self.test_movie["id"],
                "media_type": self.test_movie.get("media_type", "movie"),
                "action": "like",
                "movie_title": self.test_movie["title"],
                "movie_poster": self.test_movie.get("poster_path")
            }
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.post(f"{self.base_url}/swipe", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    match_created = data.get("match_created", False)
                    self.log_test("Submit Swipe (Like)", True, 
                                f"Liked '{self.test_movie['title']}', Match created: {match_created}")
                    return True
                else:
                    self.log_test("Submit Swipe (Like)", False, "Invalid response format")
                    return False
            else:
                self.log_test("Submit Swipe (Like)", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Submit Swipe (Like)", False, f"Error: {str(e)}")
            return False

    def test_submit_swipe_like_friend(self):
        """Test friend also liking the same movie to create a match"""
        try:
            if not self.friend_auth_token or not hasattr(self, 'test_movie') or not hasattr(self, 'swipe_session_id'):
                self.log_test("Submit Swipe (Like) - Friend", False, "Missing friend authentication, session ID, or test movie")
                return False
                
            payload = {
                "session_id": self.swipe_session_id,
                "movie_id": self.test_movie["id"],
                "media_type": self.test_movie.get("media_type", "movie"),
                "action": "like",
                "movie_title": self.test_movie["title"],
                "movie_poster": self.test_movie.get("poster_path")
            }
            headers = {"Authorization": f"Bearer {self.friend_auth_token}"}
            response = self.session.post(f"{self.base_url}/swipe", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    match_created = data.get("match_created", False)
                    self.log_test("Submit Swipe (Like) - Friend", True, 
                                f"Friend liked '{self.test_movie['title']}', Match created: {match_created}")
                    return True
                else:
                    self.log_test("Submit Swipe (Like) - Friend", False, "Invalid response format")
                    return False
            else:
                self.log_test("Submit Swipe (Like) - Friend", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Submit Swipe (Like) - Friend", False, f"Error: {str(e)}")
            return False

    def test_get_matches(self):
        """Test GET /api/swipe/matches/{session_id} - Get matches for session"""
        try:
            if not self.auth_token or not hasattr(self, 'swipe_session_id'):
                self.log_test("Get Matches", False, "Missing authentication or session ID")
                return False
                
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{self.base_url}/swipe/matches/{self.swipe_session_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Matches", True, f"Retrieved {len(data)} matches")
                    return True
                else:
                    self.log_test("Get Matches", False, "Invalid response format")
                    return False
            else:
                self.log_test("Get Matches", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Matches", False, f"Error: {str(e)}")
            return False

    def test_get_session_summary(self):
        """Test GET /api/swipe/summary/{session_id} - Get session summary"""
        try:
            if not self.auth_token or not hasattr(self, 'swipe_session_id'):
                self.log_test("Get Session Summary", False, "Missing authentication or session ID")
                return False
                
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{self.base_url}/swipe/summary/{self.swipe_session_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "total_swipes" in data and "total_matches" in data:
                    self.log_test("Get Session Summary", True, 
                                f"Session summary - Total swipes: {data['total_swipes']}, Total matches: {data['total_matches']}")
                    return True
                else:
                    self.log_test("Get Session Summary", False, "Invalid response format")
                    return False
            else:
                self.log_test("Get Session Summary", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Session Summary", False, f"Error: {str(e)}")
            return False

    def test_get_swipe_sessions(self):
        """Test GET /api/swipe/sessions - Get all swipe sessions"""
        try:
            if not self.auth_token:
                self.log_test("Get Swipe Sessions", False, "Missing authentication")
                return False
                
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{self.base_url}/swipe/sessions", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Swipe Sessions", True, f"Retrieved {len(data)} swipe sessions")
                    return True
                else:
                    self.log_test("Get Swipe Sessions", False, "Invalid response format")
                    return False
            else:
                self.log_test("Get Swipe Sessions", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Swipe Sessions", False, f"Error: {str(e)}")
            return False
    
    def test_search_by_title(self):
        """Test search with query='Inception' scope='title'"""
        try:
            payload = {
                "query": "Inception",
                "scope": "title",
                "page": 1
            }
            response = self.session.post(f"{self.base_url}/search", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data and len(data["results"]) > 0:
                    # Check if Inception is in results
                    inception_found = any("Inception" in result.get("title", "") for result in data["results"])
                    if inception_found:
                        self.log_test("Search by Title (Inception)", True, f"Found {len(data['results'])} results including Inception")
                        return True
                    else:
                        self.log_test("Search by Title (Inception)", False, f"Inception not found in {len(data['results'])} results")
                        return False
                else:
                    self.log_test("Search by Title (Inception)", False, "No results returned")
                    return False
            else:
                self.log_test("Search by Title (Inception)", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Search by Title (Inception)", False, f"Error: {str(e)}")
            return False
    
    def test_search_by_genre(self):
        """Test search with query='crime' scope='genre'"""
        try:
            payload = {
                "query": "crime",
                "scope": "genre",
                "page": 1
            }
            response = self.session.post(f"{self.base_url}/search", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_test("Search by Genre (Crime)", True, f"Found {len(data['results'])} crime movies")
                    return True
                else:
                    self.log_test("Search by Genre (Crime)", False, "Invalid response format")
                    return False
            else:
                self.log_test("Search by Genre (Crime)", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Search by Genre (Crime)", False, f"Error: {str(e)}")
            return False
    
    def test_search_by_cast(self):
        """Test search with query='Leonardo DiCaprio' scope='cast'"""
        try:
            payload = {
                "query": "Leonardo DiCaprio",
                "scope": "cast",
                "page": 1
            }
            response = self.session.post(f"{self.base_url}/search", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_test("Search by Cast (Leonardo DiCaprio)", True, f"Found {len(data['results'])} movies with Leonardo DiCaprio")
                    return True
                else:
                    self.log_test("Search by Cast (Leonardo DiCaprio)", False, "Invalid response format")
                    return False
            else:
                self.log_test("Search by Cast (Leonardo DiCaprio)", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Search by Cast (Leonardo DiCaprio)", False, f"Error: {str(e)}")
            return False
    
    def test_search_by_director(self):
        """Test search with query='Christopher Nolan' scope='director'"""
        try:
            payload = {
                "query": "Christopher Nolan",
                "scope": "director",
                "page": 1
            }
            response = self.session.post(f"{self.base_url}/search", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_test("Search by Director (Christopher Nolan)", True, f"Found {len(data['results'])} movies directed by Christopher Nolan")
                    return True
                else:
                    self.log_test("Search by Director (Christopher Nolan)", False, "Invalid response format")
                    return False
            else:
                self.log_test("Search by Director (Christopher Nolan)", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Search by Director (Christopher Nolan)", False, f"Error: {str(e)}")
            return False
    
    def test_title_details_movie(self):
        """Test title details for movie ID 27205 (Inception)"""
        try:
            response = self.session.get(f"{self.base_url}/title/27205?media_type=movie")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "title", "year", "media_type", "ratings", "hit_flop_status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check ratings structure
                    ratings = data.get("ratings", {})
                    has_ratings = any(ratings.get(key) for key in ["imdb", "rotten_tomatoes_critics", "metacritic"])
                    
                    if has_ratings:
                        self.log_test("Title Details Movie (Inception)", True, 
                                    f"Retrieved details for '{data['title']}' ({data['year']}) with ratings and hit/flop status: {data['hit_flop_status']}")
                        return True
                    else:
                        self.log_test("Title Details Movie (Inception)", False, "No ratings data found")
                        return False
                else:
                    self.log_test("Title Details Movie (Inception)", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Title Details Movie (Inception)", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Title Details Movie (Inception)", False, f"Error: {str(e)}")
            return False
    
    def test_title_details_tv(self):
        """Test title details for TV show ID 1396 (Breaking Bad)"""
        try:
            response = self.session.get(f"{self.base_url}/title/1396?media_type=tv")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "title", "year", "media_type", "ratings", "seasons", "episodes"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check ratings structure
                    ratings = data.get("ratings", {})
                    has_ratings = any(ratings.get(key) for key in ["imdb", "rotten_tomatoes_critics", "metacritic"])
                    
                    if has_ratings:
                        self.log_test("Title Details TV (Breaking Bad)", True, 
                                    f"Retrieved details for '{data['title']}' ({data['year']}) - {data['seasons']} seasons, {data['episodes']} episodes")
                        return True
                    else:
                        self.log_test("Title Details TV (Breaking Bad)", False, "No ratings data found")
                        return False
                else:
                    self.log_test("Title Details TV (Breaking Bad)", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Title Details TV (Breaking Bad)", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Title Details TV (Breaking Bad)", False, f"Error: {str(e)}")
            return False
    
    def test_streaming_availability_movie(self):
        """Test streaming availability for movie (Inception)"""
        try:
            response = self.session.get(f"{self.base_url}/streaming/27205?media_type=movie")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["available", "stream", "rent", "buy"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    if data["available"]:
                        total_options = len(data["stream"]) + len(data["rent"]) + len(data["buy"])
                        self.log_test("Streaming Availability Movie", True, 
                                    f"Found streaming options - Stream: {len(data['stream'])}, Rent: {len(data['rent'])}, Buy: {len(data['buy'])}")
                    else:
                        self.log_test("Streaming Availability Movie", True, "No streaming options available (graceful handling)")
                    return True
                else:
                    self.log_test("Streaming Availability Movie", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Streaming Availability Movie", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Streaming Availability Movie", False, f"Error: {str(e)}")
            return False
    
    def test_streaming_availability_tv(self):
        """Test streaming availability for TV show (Breaking Bad)"""
        try:
            response = self.session.get(f"{self.base_url}/streaming/1396?media_type=tv")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["available", "stream", "rent", "buy"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    if data["available"]:
                        total_options = len(data["stream"]) + len(data["rent"]) + len(data["buy"])
                        self.log_test("Streaming Availability TV", True, 
                                    f"Found streaming options - Stream: {len(data['stream'])}, Rent: {len(data['rent'])}, Buy: {len(data['buy'])}")
                    else:
                        self.log_test("Streaming Availability TV", True, "No streaming options available (graceful handling)")
                    return True
                else:
                    self.log_test("Streaming Availability TV", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Streaming Availability TV", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Streaming Availability TV", False, f"Error: {str(e)}")
            return False
    
    def test_popular_titles(self):
        """Test popular titles endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/popular")
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data and len(data["results"]) > 0:
                    self.log_test("Popular Titles", True, f"Retrieved {len(data['results'])} popular titles")
                    return True
                else:
                    self.log_test("Popular Titles", False, "No popular titles returned")
                    return False
            else:
                self.log_test("Popular Titles", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Popular Titles", False, f"Error: {str(e)}")
            return False
    
    def test_search_history_creation_and_retrieval(self):
        """Test search history creation and retrieval"""
        try:
            # First, clear existing history
            clear_response = self.session.delete(f"{self.base_url}/search/history")
            
            # Perform a search to create history
            search_payload = {
                "query": "Test Movie",
                "scope": "title",
                "page": 1
            }
            search_response = self.session.post(f"{self.base_url}/search", json=search_payload)
            
            if search_response.status_code == 200:
                # Now check history
                history_response = self.session.get(f"{self.base_url}/search/history")
                
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    if len(history_data) > 0 and history_data[0]["query"] == "Test Movie":
                        self.log_test("Search History Creation & Retrieval", True, f"Found {len(history_data)} history items")
                        return True
                    else:
                        self.log_test("Search History Creation & Retrieval", False, "Search not found in history")
                        return False
                else:
                    self.log_test("Search History Creation & Retrieval", False, f"History retrieval failed: HTTP {history_response.status_code}")
                    return False
            else:
                self.log_test("Search History Creation & Retrieval", False, f"Search failed: HTTP {search_response.status_code}")
                return False
        except Exception as e:
            self.log_test("Search History Creation & Retrieval", False, f"Error: {str(e)}")
            return False
    
    def test_clear_search_history(self):
        """Test clearing search history"""
        try:
            response = self.session.delete(f"{self.base_url}/search/history")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    # Verify history is actually cleared
                    history_response = self.session.get(f"{self.base_url}/search/history")
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        if len(history_data) == 0:
                            self.log_test("Clear Search History", True, "Search history cleared successfully")
                            return True
                        else:
                            self.log_test("Clear Search History", False, f"History not cleared - still has {len(history_data)} items")
                            return False
                    else:
                        self.log_test("Clear Search History", False, "Could not verify history clearing")
                        return False
                else:
                    self.log_test("Clear Search History", False, "Invalid response format")
                    return False
            else:
                self.log_test("Clear Search History", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Clear Search History", False, f"Error: {str(e)}")
            return False
    
    def test_genres(self):
        """Test genres endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/genres")
            
            if response.status_code == 200:
                data = response.json()
                if "genres" in data and len(data["genres"]) > 0:
                    self.log_test("Genres", True, f"Retrieved {len(data['genres'])} genres")
                    return True
                else:
                    self.log_test("Genres", False, "No genres returned")
                    return False
            else:
                self.log_test("Genres", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Genres", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"🚀 Starting FindFlix API Tests with Tinder Functionality")
        print(f"Backend URL: {self.base_url}")
        print("=" * 70)
        
        # Authentication and Friend System Tests (New Tinder Features)
        auth_tests = [
            self.test_health_check,
            self.test_user_registration,
            self.test_user_login,
            self.test_get_current_user,
            self.test_friend_user_registration,
            self.test_send_friend_request,
            self.test_get_friend_requests,
            self.test_accept_friend_request,
            self.test_get_friends_list,
        ]
        
        # Swipe Session Tests (Core Tinder Functionality)
        swipe_tests = [
            self.test_create_swipe_session,
            self.test_get_swipe_content,
            self.test_submit_swipe_like,
            self.test_submit_swipe_like_friend,
            self.test_get_matches,
            self.test_get_session_summary,
            self.test_get_swipe_sessions,
            self.test_logout
        ]
        
        # Original Movie API Tests (Backward Compatibility)
        movie_tests = [
            self.test_search_by_title,
            self.test_search_by_genre,
            self.test_search_by_cast,
            self.test_search_by_director,
            self.test_title_details_movie,
            self.test_title_details_tv,
            self.test_streaming_availability_movie,
            self.test_streaming_availability_tv,
            self.test_popular_titles,
            self.test_search_history_creation_and_retrieval,
            self.test_clear_search_history,
            self.test_genres
        ]
        
        all_tests = auth_tests + swipe_tests + movie_tests
        
        passed = 0
        failed = 0
        
        print("\n🔐 Testing Authentication & Friend System:")
        print("-" * 70)
        for test in auth_tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        print(f"\n🎯 Testing Swipe Session Endpoints (Core Tinder Features):")
        print("-" * 70)
        for test in swipe_tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        print(f"\n🎬 Testing Movie API Compatibility (Original Features):")
        print("-" * 70)
        for test in movie_tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        print("=" * 70)
        print(f"📊 Final Test Results: {passed} passed, {failed} failed")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed, failed, self.test_results

if __name__ == "__main__":
    tester = FindFlixAPITester()
    passed, failed, results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    sys.exit(1 if failed > 0 else 0)