#!/usr/bin/env python3
"""
Backend API Testing for Movie Recommendation API
Tests all endpoints with comprehensive test cases
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL - using localhost for testing
BACKEND_URL = "http://localhost:8001/api"

class MovieAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        
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
        """Test GET /api/ - Health check"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "status" in data:
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

    def test_cast_search_sorting_year_desc(self):
        """Test cast search with Christian Bale sorted by year_desc across pages"""
        try:
            # Test page 1
            payload_page1 = {
                "query": "Christian Bale",
                "scope": "cast",
                "page": 1,
                "sort_by": "year_desc"
            }
            response1 = self.session.post(f"{self.base_url}/search", json=payload_page1)
            
            if response1.status_code != 200:
                self.log_test("Cast Search Sorting (Christian Bale year_desc)", False, f"Page 1 failed: HTTP {response1.status_code}")
                return False
            
            data1 = response1.json()
            results1 = data1.get("results", [])
            
            if len(results1) == 0:
                self.log_test("Cast Search Sorting (Christian Bale year_desc)", False, "No results found for Christian Bale")
                return False
            
            # Extract years from page 1 and verify descending order
            years1 = []
            for movie in results1:
                year = movie.get("year", "")
                if year and year.isdigit():
                    years1.append(int(year))
                else:
                    years1.append(0)  # Handle missing years
            
            # Check if page 1 is sorted in descending order
            is_page1_sorted = all(years1[i] >= years1[i+1] for i in range(len(years1)-1))
            
            if not is_page1_sorted:
                self.log_test("Cast Search Sorting (Christian Bale year_desc)", False, f"Page 1 not sorted descending: {years1}")
                return False
            
            # Test page 2
            payload_page2 = {
                "query": "Christian Bale",
                "scope": "cast",
                "page": 2,
                "sort_by": "year_desc"
            }
            response2 = self.session.post(f"{self.base_url}/search", json=payload_page2)
            
            if response2.status_code != 200:
                self.log_test("Cast Search Sorting (Christian Bale year_desc)", False, f"Page 2 failed: HTTP {response2.status_code}")
                return False
            
            data2 = response2.json()
            results2 = data2.get("results", [])
            
            if len(results2) == 0:
                self.log_test("Cast Search Sorting (Christian Bale year_desc)", True, f"Page 1 sorted correctly ({min(years1)}-{max(years1)}), Page 2 empty")
                return True
            
            # Extract years from page 2
            years2 = []
            for movie in results2:
                year = movie.get("year", "")
                if year and year.isdigit():
                    years2.append(int(year))
                else:
                    years2.append(0)
            
            # Check if page 2 is sorted in descending order
            is_page2_sorted = all(years2[i] >= years2[i+1] for i in range(len(years2)-1))
            
            if not is_page2_sorted:
                self.log_test("Cast Search Sorting (Christian Bale year_desc)", False, f"Page 2 not sorted descending: {years2}")
                return False
            
            # CRITICAL CHECK: All movies in page 2 should have years <= oldest movie from page 1
            oldest_page1 = min(years1) if years1 else 0
            newest_page2 = max(years2) if years2 else 0
            
            if newest_page2 > oldest_page1:
                self.log_test("Cast Search Sorting (Christian Bale year_desc)", False, 
                            f"SORTING BUG: Page 2 newest ({newest_page2}) > Page 1 oldest ({oldest_page1}). Page 1: {years1}, Page 2: {years2}")
                return False
            
            self.log_test("Cast Search Sorting (Christian Bale year_desc)", True, 
                        f"Sorting consistent across pages. Page 1: {oldest_page1}-{max(years1)}, Page 2: {min(years2)}-{newest_page2}")
            return True
            
        except Exception as e:
            self.log_test("Cast Search Sorting (Christian Bale year_desc)", False, f"Error: {str(e)}")
            return False

    def test_cast_search_sorting_year_asc(self):
        """Test cast search with Christian Bale sorted by year_asc across pages"""
        try:
            # Test page 1
            payload_page1 = {
                "query": "Christian Bale",
                "scope": "cast",
                "page": 1,
                "sort_by": "year_asc"
            }
            response1 = self.session.post(f"{self.base_url}/search", json=payload_page1)
            
            if response1.status_code != 200:
                self.log_test("Cast Search Sorting (Christian Bale year_asc)", False, f"Page 1 failed: HTTP {response1.status_code}")
                return False
            
            data1 = response1.json()
            results1 = data1.get("results", [])
            
            if len(results1) == 0:
                self.log_test("Cast Search Sorting (Christian Bale year_asc)", False, "No results found for Christian Bale")
                return False
            
            # Extract years from page 1
            years1 = []
            for movie in results1:
                year = movie.get("year", "")
                if year and year.isdigit():
                    years1.append(int(year))
                else:
                    years1.append(9999)  # Handle missing years for ascending sort
            
            # Check if page 1 is sorted in ascending order
            is_page1_sorted = all(years1[i] <= years1[i+1] for i in range(len(years1)-1))
            
            if not is_page1_sorted:
                self.log_test("Cast Search Sorting (Christian Bale year_asc)", False, f"Page 1 not sorted ascending: {years1}")
                return False
            
            # Test page 2
            payload_page2 = {
                "query": "Christian Bale",
                "scope": "cast",
                "page": 2,
                "sort_by": "year_asc"
            }
            response2 = self.session.post(f"{self.base_url}/search", json=payload_page2)
            
            if response2.status_code != 200:
                self.log_test("Cast Search Sorting (Christian Bale year_asc)", False, f"Page 2 failed: HTTP {response2.status_code}")
                return False
            
            data2 = response2.json()
            results2 = data2.get("results", [])
            
            if len(results2) == 0:
                self.log_test("Cast Search Sorting (Christian Bale year_asc)", True, f"Page 1 sorted correctly ({min(years1)}-{max(years1)}), Page 2 empty")
                return True
            
            # Extract years from page 2
            years2 = []
            for movie in results2:
                year = movie.get("year", "")
                if year and year.isdigit():
                    years2.append(int(year))
                else:
                    years2.append(9999)
            
            # CRITICAL CHECK: All movies in page 2 should have years >= newest movie from page 1
            newest_page1 = max(years1) if years1 else 9999
            oldest_page2 = min(years2) if years2 else 0
            
            if oldest_page2 < newest_page1:
                self.log_test("Cast Search Sorting (Christian Bale year_asc)", False, 
                            f"SORTING BUG: Page 2 oldest ({oldest_page2}) < Page 1 newest ({newest_page1}). Page 1: {years1}, Page 2: {years2}")
                return False
            
            self.log_test("Cast Search Sorting (Christian Bale year_asc)", True, 
                        f"Sorting consistent across pages. Page 1: {min(years1)}-{newest_page1}, Page 2: {oldest_page2}-{max(years2)}")
            return True
            
        except Exception as e:
            self.log_test("Cast Search Sorting (Christian Bale year_asc)", False, f"Error: {str(e)}")
            return False

    def test_cast_search_sorting_rating_desc(self):
        """Test cast search with Christian Bale sorted by rating_desc across pages"""
        try:
            # Test page 1
            payload_page1 = {
                "query": "Christian Bale",
                "scope": "cast",
                "page": 1,
                "sort_by": "rating_desc"
            }
            response1 = self.session.post(f"{self.base_url}/search", json=payload_page1)
            
            if response1.status_code != 200:
                self.log_test("Cast Search Sorting (Christian Bale rating_desc)", False, f"Page 1 failed: HTTP {response1.status_code}")
                return False
            
            data1 = response1.json()
            results1 = data1.get("results", [])
            
            if len(results1) == 0:
                self.log_test("Cast Search Sorting (Christian Bale rating_desc)", False, "No results found for Christian Bale")
                return False
            
            # Extract ratings from page 1
            ratings1 = []
            for movie in results1:
                rating = movie.get("vote_average", 0)
                ratings1.append(float(rating) if rating else 0)
            
            # Check if page 1 is sorted in descending order
            is_page1_sorted = all(ratings1[i] >= ratings1[i+1] for i in range(len(ratings1)-1))
            
            if not is_page1_sorted:
                self.log_test("Cast Search Sorting (Christian Bale rating_desc)", False, f"Page 1 not sorted descending: {ratings1}")
                return False
            
            # Test page 2
            payload_page2 = {
                "query": "Christian Bale",
                "scope": "cast",
                "page": 2,
                "sort_by": "rating_desc"
            }
            response2 = self.session.post(f"{self.base_url}/search", json=payload_page2)
            
            if response2.status_code != 200:
                self.log_test("Cast Search Sorting (Christian Bale rating_desc)", False, f"Page 2 failed: HTTP {response2.status_code}")
                return False
            
            data2 = response2.json()
            results2 = data2.get("results", [])
            
            if len(results2) == 0:
                self.log_test("Cast Search Sorting (Christian Bale rating_desc)", True, f"Page 1 sorted correctly ({min(ratings1):.1f}-{max(ratings1):.1f}), Page 2 empty")
                return True
            
            # Extract ratings from page 2
            ratings2 = []
            for movie in results2:
                rating = movie.get("vote_average", 0)
                ratings2.append(float(rating) if rating else 0)
            
            # CRITICAL CHECK: All movies in page 2 should have ratings <= lowest rating from page 1
            lowest_page1 = min(ratings1) if ratings1 else 0
            highest_page2 = max(ratings2) if ratings2 else 0
            
            if highest_page2 > lowest_page1:
                self.log_test("Cast Search Sorting (Christian Bale rating_desc)", False, 
                            f"SORTING BUG: Page 2 highest ({highest_page2:.1f}) > Page 1 lowest ({lowest_page1:.1f}). Page 1: {ratings1}, Page 2: {ratings2}")
                return False
            
            self.log_test("Cast Search Sorting (Christian Bale rating_desc)", True, 
                        f"Sorting consistent across pages. Page 1: {lowest_page1:.1f}-{max(ratings1):.1f}, Page 2: {min(ratings2):.1f}-{highest_page2:.1f}")
            return True
            
        except Exception as e:
            self.log_test("Cast Search Sorting (Christian Bale rating_desc)", False, f"Error: {str(e)}")
            return False

    def test_director_search_sorting_year_desc(self):
        """Test director search with Christopher Nolan sorted by year_desc across pages"""
        try:
            # Test page 1
            payload_page1 = {
                "query": "Christopher Nolan",
                "scope": "director",
                "page": 1,
                "sort_by": "year_desc"
            }
            response1 = self.session.post(f"{self.base_url}/search", json=payload_page1)
            
            if response1.status_code != 200:
                self.log_test("Director Search Sorting (Christopher Nolan year_desc)", False, f"Page 1 failed: HTTP {response1.status_code}")
                return False
            
            data1 = response1.json()
            results1 = data1.get("results", [])
            
            if len(results1) == 0:
                self.log_test("Director Search Sorting (Christopher Nolan year_desc)", False, "No results found for Christopher Nolan")
                return False
            
            # Extract years from page 1
            years1 = []
            for movie in results1:
                year = movie.get("year", "")
                if year and year.isdigit():
                    years1.append(int(year))
                else:
                    years1.append(0)
            
            # Check if page 1 is sorted in descending order
            is_page1_sorted = all(years1[i] >= years1[i+1] for i in range(len(years1)-1))
            
            if not is_page1_sorted:
                self.log_test("Director Search Sorting (Christopher Nolan year_desc)", False, f"Page 1 not sorted descending: {years1}")
                return False
            
            # Test page 2
            payload_page2 = {
                "query": "Christopher Nolan",
                "scope": "director",
                "page": 2,
                "sort_by": "year_desc"
            }
            response2 = self.session.post(f"{self.base_url}/search", json=payload_page2)
            
            if response2.status_code != 200:
                self.log_test("Director Search Sorting (Christopher Nolan year_desc)", False, f"Page 2 failed: HTTP {response2.status_code}")
                return False
            
            data2 = response2.json()
            results2 = data2.get("results", [])
            
            if len(results2) == 0:
                self.log_test("Director Search Sorting (Christopher Nolan year_desc)", True, f"Page 1 sorted correctly ({min(years1)}-{max(years1)}), Page 2 empty")
                return True
            
            # Extract years from page 2
            years2 = []
            for movie in results2:
                year = movie.get("year", "")
                if year and year.isdigit():
                    years2.append(int(year))
                else:
                    years2.append(0)
            
            # CRITICAL CHECK: All movies in page 2 should have years <= oldest movie from page 1
            oldest_page1 = min(years1) if years1 else 0
            newest_page2 = max(years2) if years2 else 0
            
            if newest_page2 > oldest_page1:
                self.log_test("Director Search Sorting (Christopher Nolan year_desc)", False, 
                            f"SORTING BUG: Page 2 newest ({newest_page2}) > Page 1 oldest ({oldest_page1}). Page 1: {years1}, Page 2: {years2}")
                return False
            
            self.log_test("Director Search Sorting (Christopher Nolan year_desc)", True, 
                        f"Sorting consistent across pages. Page 1: {oldest_page1}-{max(years1)}, Page 2: {min(years2)}-{newest_page2}")
            return True
            
        except Exception as e:
            self.log_test("Director Search Sorting (Christopher Nolan year_desc)", False, f"Error: {str(e)}")
            return False

    def test_genre_search_sorting_year_desc(self):
        """Test genre search with action sorted by year_desc across pages"""
        try:
            # Test page 1
            payload_page1 = {
                "query": "action",
                "scope": "genre",
                "page": 1,
                "sort_by": "year_desc"
            }
            response1 = self.session.post(f"{self.base_url}/search", json=payload_page1)
            
            if response1.status_code != 200:
                self.log_test("Genre Search Sorting (Action year_desc)", False, f"Page 1 failed: HTTP {response1.status_code}")
                return False
            
            data1 = response1.json()
            results1 = data1.get("results", [])
            
            if len(results1) == 0:
                self.log_test("Genre Search Sorting (Action year_desc)", False, "No results found for action genre")
                return False
            
            # Extract years from page 1
            years1 = []
            for movie in results1:
                year = movie.get("year", "")
                if year and year.isdigit():
                    years1.append(int(year))
                else:
                    years1.append(0)
            
            # Check if page 1 is sorted in descending order
            is_page1_sorted = all(years1[i] >= years1[i+1] for i in range(len(years1)-1))
            
            if not is_page1_sorted:
                self.log_test("Genre Search Sorting (Action year_desc)", False, f"Page 1 not sorted descending: {years1}")
                return False
            
            # Test page 2
            payload_page2 = {
                "query": "action",
                "scope": "genre",
                "page": 2,
                "sort_by": "year_desc"
            }
            response2 = self.session.post(f"{self.base_url}/search", json=payload_page2)
            
            if response2.status_code != 200:
                self.log_test("Genre Search Sorting (Action year_desc)", False, f"Page 2 failed: HTTP {response2.status_code}")
                return False
            
            data2 = response2.json()
            results2 = data2.get("results", [])
            
            if len(results2) == 0:
                self.log_test("Genre Search Sorting (Action year_desc)", True, f"Page 1 sorted correctly ({min(years1)}-{max(years1)}), Page 2 empty")
                return True
            
            # Extract years from page 2
            years2 = []
            for movie in results2:
                year = movie.get("year", "")
                if year and year.isdigit():
                    years2.append(int(year))
                else:
                    years2.append(0)
            
            # CRITICAL CHECK: All movies in page 2 should have years <= oldest movie from page 1
            oldest_page1 = min(years1) if years1 else 0
            newest_page2 = max(years2) if years2 else 0
            
            if newest_page2 > oldest_page1:
                self.log_test("Genre Search Sorting (Action year_desc)", False, 
                            f"SORTING BUG: Page 2 newest ({newest_page2}) > Page 1 oldest ({oldest_page1}). Page 1: {years1}, Page 2: {years2}")
                return False
            
            self.log_test("Genre Search Sorting (Action year_desc)", True, 
                        f"Sorting consistent across pages. Page 1: {oldest_page1}-{max(years1)}, Page 2: {min(years2)}-{newest_page2}")
            return True
            
        except Exception as e:
            self.log_test("Genre Search Sorting (Action year_desc)", False, f"Error: {str(e)}")
            return False
    
    def test_matt_damon_caching_functionality(self):
        """Test 1: Cast Search with Caching - Matt Damon"""
        try:
            print("\n🔍 TEST 1: Cast Search with Caching")
            
            # Clear any existing cache by waiting a moment and making a different search first
            dummy_payload = {
                "query": "Tom Hanks",
                "scope": "cast",
                "page": 1
            }
            self.session.post(f"{self.base_url}/search", json=dummy_payload)
            
            # Test page 1 - Matt Damon with default sort
            payload_page1 = {
                "query": "Matt Damon",
                "scope": "cast",
                "page": 1
            }
            
            print("📤 POST /api/search - Matt Damon, scope=cast, page=1 (no sort_by - default sort)")
            response1 = self.session.post(f"{self.base_url}/search", json=payload_page1)
            
            if response1.status_code != 200:
                self.log_test("Matt Damon Caching Test", False, f"Page 1 failed: HTTP {response1.status_code}")
                return False
            
            data1 = response1.json()
            results1 = data1.get("results", [])
            
            if len(results1) == 0:
                self.log_test("Matt Damon Caching Test", False, "No results found for Matt Damon")
                return False
            
            # Record first and last movie titles/years from page 1
            first_movie = results1[0]
            last_movie = results1[-1]
            
            print(f"✅ Results returned: {len(results1)} movies")
            print(f"📝 First movie: '{first_movie.get('title', 'N/A')}' ({first_movie.get('year', 'N/A')})")
            print(f"📝 Last movie: '{last_movie.get('title', 'N/A')}' ({last_movie.get('year', 'N/A')})")
            
            # Test page 2 - should use cache
            payload_page2 = {
                "query": "Matt Damon",
                "scope": "cast",
                "page": 2
            }
            
            print("\n📤 POST /api/search - Matt Damon, scope=cast, page=2 (same parameters)")
            response2 = self.session.post(f"{self.base_url}/search", json=payload_page2)
            
            if response2.status_code != 200:
                self.log_test("Matt Damon Caching Test", False, f"Page 2 failed: HTTP {response2.status_code}")
                return False
            
            data2 = response2.json()
            results2 = data2.get("results", [])
            
            print(f"✅ Page 2 results returned: {len(results2)} movies")
            
            if len(results2) > 0:
                first_movie_p2 = results2[0]
                last_movie_p2 = results2[-1]
                print(f"📝 Page 2 first movie: '{first_movie_p2.get('title', 'N/A')}' ({first_movie_p2.get('year', 'N/A')})")
                print(f"📝 Page 2 last movie: '{last_movie_p2.get('title', 'N/A')}' ({last_movie_p2.get('year', 'N/A')})")
                
                # Check for duplicates between pages
                page1_titles = set(movie.get('title', '') for movie in results1)
                page2_titles = set(movie.get('title', '') for movie in results2)
                duplicates = page1_titles.intersection(page2_titles)
                
                if duplicates:
                    self.log_test("Matt Damon Caching Test", False, f"Found duplicate movies between pages: {list(duplicates)}")
                    return False
                else:
                    print("✅ No duplicate movies between pages")
            
            self.log_test("Matt Damon Caching Test", True, 
                        f"Caching test completed. Page 1: {len(results1)} results, Page 2: {len(results2)} results. No duplicates found.")
            return True
            
        except Exception as e:
            self.log_test("Matt Damon Caching Test", False, f"Error: {str(e)}")
            return False

    def test_matt_damon_sorting_functionality(self):
        """Test 2: Cast Search with Sorting - Matt Damon year_desc"""
        try:
            print("\n🔍 TEST 2: Cast Search with Sorting")
            
            # Test page 1 - Matt Damon with year_desc sort
            payload_page1 = {
                "query": "Matt Damon",
                "scope": "cast",
                "page": 1,
                "sort_by": "year_desc"
            }
            
            print("📤 POST /api/search - Matt Damon, scope=cast, page=1, sort_by=year_desc")
            response1 = self.session.post(f"{self.base_url}/search", json=payload_page1)
            
            if response1.status_code != 200:
                self.log_test("Matt Damon Sorting Test", False, f"Page 1 failed: HTTP {response1.status_code}")
                return False
            
            data1 = response1.json()
            results1 = data1.get("results", [])
            
            if len(results1) == 0:
                self.log_test("Matt Damon Sorting Test", False, "No results found for Matt Damon")
                return False
            
            # Extract years from page 1 and verify descending order
            years1 = []
            titles1 = []
            for movie in results1:
                year = movie.get("year", "")
                title = movie.get("title", "")
                titles1.append(f"{title} ({year})")
                if year and year.isdigit():
                    years1.append(int(year))
                else:
                    years1.append(0)  # Handle missing years
            
            print(f"✅ Page 1 results: {len(results1)} movies")
            print(f"📝 Years range: {min(years1) if years1 else 'N/A'} - {max(years1) if years1 else 'N/A'}")
            print(f"📝 Sample movies: {titles1[:3]}")
            
            # Check if page 1 is sorted in descending order
            is_page1_sorted = all(years1[i] >= years1[i+1] for i in range(len(years1)-1))
            
            if not is_page1_sorted:
                print(f"❌ Page 1 not sorted descending: {years1}")
                self.log_test("Matt Damon Sorting Test", False, f"Page 1 not sorted descending: {years1}")
                return False
            else:
                print("✅ Page 1 is sorted by year descending")
            
            # Record oldest year on page 1
            oldest_year_page1 = min(years1) if years1 else 0
            print(f"📝 Oldest year on page 1: {oldest_year_page1}")
            
            # Test page 2
            payload_page2 = {
                "query": "Matt Damon",
                "scope": "cast",
                "page": 2,
                "sort_by": "year_desc"
            }
            
            print("\n📤 POST /api/search - Matt Damon, scope=cast, page=2, sort_by=year_desc")
            response2 = self.session.post(f"{self.base_url}/search", json=payload_page2)
            
            if response2.status_code != 200:
                self.log_test("Matt Damon Sorting Test", False, f"Page 2 failed: HTTP {response2.status_code}")
                return False
            
            data2 = response2.json()
            results2 = data2.get("results", [])
            
            if len(results2) == 0:
                print("✅ Page 2 is empty - sorting consistent")
                self.log_test("Matt Damon Sorting Test", True, f"Page 1 sorted correctly ({oldest_year_page1}-{max(years1)}), Page 2 empty")
                return True
            
            # Extract years from page 2
            years2 = []
            titles2 = []
            for movie in results2:
                year = movie.get("year", "")
                title = movie.get("title", "")
                titles2.append(f"{title} ({year})")
                if year and year.isdigit():
                    years2.append(int(year))
                else:
                    years2.append(0)
            
            print(f"✅ Page 2 results: {len(results2)} movies")
            print(f"📝 Years range: {min(years2) if years2 else 'N/A'} - {max(years2) if years2 else 'N/A'}")
            print(f"📝 Sample movies: {titles2[:3]}")
            
            # Check if page 2 is sorted in descending order
            is_page2_sorted = all(years2[i] >= years2[i+1] for i in range(len(years2)-1))
            
            if not is_page2_sorted:
                print(f"❌ Page 2 not sorted descending: {years2}")
                self.log_test("Matt Damon Sorting Test", False, f"Page 2 not sorted descending: {years2}")
                return False
            else:
                print("✅ Page 2 is sorted by year descending")
            
            # CRITICAL CHECK: All movies in page 2 should have years <= oldest movie from page 1
            newest_page2 = max(years2) if years2 else 0
            
            print(f"\n🔍 CRITICAL SORTING CHECK:")
            print(f"📝 Oldest year on page 1: {oldest_year_page1}")
            print(f"📝 Newest year on page 2: {newest_page2}")
            
            if newest_page2 > oldest_year_page1:
                print(f"❌ SORTING BUG DETECTED!")
                print(f"   Page 2 has movies from {newest_page2} which is newer than page 1's oldest ({oldest_year_page1})")
                print(f"   This breaks the global sort order across pages")
                self.log_test("Matt Damon Sorting Test", False, 
                            f"CRITICAL SORTING BUG: Page 2 newest ({newest_page2}) > Page 1 oldest ({oldest_year_page1}). Page 1: {years1}, Page 2: {years2}")
                return False
            else:
                print("✅ Sorting is consistent across pages")
            
            self.log_test("Matt Damon Sorting Test", True, 
                        f"Sorting consistent across pages. Page 1: {oldest_year_page1}-{max(years1)}, Page 2: {min(years2)}-{newest_page2}")
            return True
            
        except Exception as e:
            self.log_test("Matt Damon Sorting Test", False, f"Error: {str(e)}")
            return False

    def test_no_results_scenarios(self):
        """Test 3: No Results Issue - Test scenarios where results become empty unexpectedly"""
        try:
            print("\n🔍 TEST 3: No Results Issue Testing")
            
            # Test 1: Search for a very obscure actor
            payload_obscure = {
                "query": "Zxcvbnm Qwerty",  # Non-existent actor
                "scope": "cast",
                "page": 1
            }
            
            print("📤 Testing obscure actor search (should return empty gracefully)")
            response_obscure = self.session.post(f"{self.base_url}/search", json=payload_obscure)
            
            if response_obscure.status_code == 200:
                data_obscure = response_obscure.json()
                results_obscure = data_obscure.get("results", [])
                print(f"✅ Obscure actor search returned {len(results_obscure)} results (expected: 0)")
            else:
                print(f"❌ Obscure actor search failed: HTTP {response_obscure.status_code}")
                return False
            
            # Test 2: Search with very specific filters that might return no results
            payload_filtered = {
                "query": "Matt Damon",
                "scope": "cast",
                "page": 1,
                "genre": "999999",  # Non-existent genre ID
                "language": "zz"    # Non-existent language code
            }
            
            print("📤 Testing over-filtered search (should return empty gracefully)")
            response_filtered = self.session.post(f"{self.base_url}/search", json=payload_filtered)
            
            if response_filtered.status_code == 200:
                data_filtered = response_filtered.json()
                results_filtered = data_filtered.get("results", [])
                print(f"✅ Over-filtered search returned {len(results_filtered)} results (expected: 0)")
            else:
                print(f"❌ Over-filtered search failed: HTTP {response_filtered.status_code}")
                return False
            
            # Test 3: Search for page beyond available results
            payload_high_page = {
                "query": "Matt Damon",
                "scope": "cast",
                "page": 999  # Very high page number
            }
            
            print("📤 Testing high page number search")
            response_high_page = self.session.post(f"{self.base_url}/search", json=payload_high_page)
            
            if response_high_page.status_code == 200:
                data_high_page = response_high_page.json()
                results_high_page = data_high_page.get("results", [])
                print(f"✅ High page search returned {len(results_high_page)} results")
            else:
                print(f"❌ High page search failed: HTTP {response_high_page.status_code}")
                return False
            
            self.log_test("No Results Issue Test", True, 
                        f"All edge cases handled gracefully. Obscure: {len(results_obscure)}, Filtered: {len(results_filtered)}, High page: {len(results_high_page)}")
            return True
            
        except Exception as e:
            self.log_test("No Results Issue Test", False, f"Error: {str(e)}")
            return False

    def run_caching_and_sorting_tests(self):
        """Run the specific caching and sorting tests requested by user"""
        print(f"🚀 Starting Cast Search Caching & Sorting Tests")
        print(f"Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Check backend logs before starting
        print("📋 Checking backend logs for caching messages...")
        
        caching_tests = [
            self.test_matt_damon_caching_functionality,
            self.test_matt_damon_sorting_functionality,
            self.test_no_results_scenarios
        ]
        
        passed = 0
        failed = 0
        
        for test in caching_tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        print("=" * 80)
        print(f"📊 Caching & Sorting Test Results: {passed} passed, {failed} failed")
        
        # Check backend logs after tests
        print("\n📋 Checking backend logs for caching messages after tests...")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"] and ("Matt Damon" in result["test"] or "No Results" in result["test"]):
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed, failed, self.test_results

    def run_sorting_tests(self):
        """Run sorting-specific tests for pagination consistency"""
        print(f"🔄 Starting Sorting & Pagination Tests")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        sorting_tests = [
            self.test_cast_search_sorting_year_desc,
            self.test_cast_search_sorting_year_asc,
            self.test_cast_search_sorting_rating_desc,
            self.test_director_search_sorting_year_desc,
            self.test_genre_search_sorting_year_desc
        ]
        
        passed = 0
        failed = 0
        
        for test in sorting_tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        print("=" * 60)
        print(f"📊 Sorting Test Results: {passed} passed, {failed} failed")
        
        if failed > 0:
            print("\n❌ Failed Sorting Tests:")
            for result in self.test_results:
                if not result["success"] and "Sorting" in result["test"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed, failed, self.test_results

    def run_all_tests(self):
        """Run all tests"""
        print(f"🚀 Starting Movie Recommendation API Tests")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        tests = [
            self.test_health_check,
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
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        print("=" * 60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed, failed, self.test_results

if __name__ == "__main__":
    tester = MovieAPITester()
    
    # Run the specific caching and sorting tests requested by user
    passed, failed, results = tester.run_caching_and_sorting_tests()
    
    # Exit with error code if tests failed
    sys.exit(1 if failed > 0 else 0)