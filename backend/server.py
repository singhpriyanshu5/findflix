from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import httpx
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# API Keys
TMDB_API_KEY = os.environ['TMDB_API_KEY']
RAPIDAPI_KEY = os.environ['RAPIDAPI_KEY']
OMDB_API_KEY = os.environ['OMDB_API_KEY']
WATCHMODE_API_KEY = os.environ['WATCHMODE_API_KEY']

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== Models =====
class SearchScope(str, Enum):
    TITLE = "title"
    GENRE = "genre"
    CAST = "cast"
    DIRECTOR = "director"

class SearchHistoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    scope: SearchScope
    genre: Optional[str] = None
    language: Optional[str] = None
    content_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SearchRequest(BaseModel):
    query: str
    scope: SearchScope = SearchScope.TITLE
    page: int = 1
    genre: Optional[str] = None  # Genre ID as string
    language: Optional[str] = None  # ISO 639-1 language code (e.g., "en", "hi", "te")
    content_type: Optional[str] = None  # "movie" or "tv"
    sort_by: Optional[str] = None  # "rating_desc", "rating_asc", "year_desc", "year_asc"

# ===== Helper Functions =====
async def fetch_tmdb_data(endpoint: str, params: Dict = None):
    """Fetch data from TMDB API"""
    base_url = "https://api.themoviedb.org/3"
    default_params = {"api_key": TMDB_API_KEY}
    if params:
        default_params.update(params)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{base_url}/{endpoint}", params=default_params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"TMDB API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"TMDB API error: {str(e)}")

async def fetch_omdb_data(imdb_id: str):
    """Fetch additional ratings from OMDb API"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                "http://www.omdbapi.com/",
                params={"apikey": OMDB_API_KEY, "i": imdb_id}
            )
            response.raise_for_status()
            data = response.json()
            if data.get("Response") == "False":
                return None
            return data
        except Exception as e:
            logger.error(f"OMDb API error: {str(e)}")
            return None

async def fetch_streaming_availability(tmdb_id: int, media_type: str):
    """Fetch US streaming availability from Streaming Availability API"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Using the show endpoint to get streaming info
            response = await client.get(
                f"https://streaming-availability.p.rapidapi.com/shows/{media_type}/{tmdb_id}",
                headers={
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com"
                },
                params={"series_granularity": "show", "output_language": "en"}
            )
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            data = response.json()
            
            # Extract US streaming options
            streaming_options = data.get("streamingOptions", {}).get("us", [])
            
            # Group by type: stream, rent, buy
            grouped = {"stream": [], "rent": [], "buy": []}
            seen_services = {"stream": set(), "rent": set(), "buy": set()}
            
            for option in streaming_options:
                service_name = option.get("service", {}).get("name", "")
                service_id = option.get("service", {}).get("id", "")
                option_type = option.get("type", "").lower()
                link = option.get("link", "")
                
                # Map type to our categories
                if option_type in ["subscription", "free"]:
                    category = "stream"
                elif option_type == "rent":
                    category = "rent"
                elif option_type == "buy":
                    category = "buy"
                else:
                    continue
                
                # Avoid duplicates
                if service_id not in seen_services[category]:
                    grouped[category].append({
                        "name": service_name,
                        "id": service_id,
                        "link": link
                    })
                    seen_services[category].add(service_id)
            
            return grouped
        except Exception as e:
            logger.error(f"Streaming API (RapidAPI) error: {str(e)}")
            return None

async def fetch_watchmode_streaming(imdb_id: str):
    """Fetch US streaming availability from WatchMode API"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # First, search for the title to get WatchMode ID
            search_response = await client.get(
                "https://api.watchmode.com/v1/search/",
                params={
                    "apiKey": WATCHMODE_API_KEY,
                    "search_field": "imdb_id",
                    "search_value": imdb_id
                }
            )
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if not search_data.get("title_results"):
                logger.info(f"WatchMode: No results for IMDb ID {imdb_id}")
                return None
            
            watchmode_id = search_data["title_results"][0]["id"]
            
            # Get sources (streaming availability)
            sources_response = await client.get(
                f"https://api.watchmode.com/v1/title/{watchmode_id}/sources/",
                params={
                    "apiKey": WATCHMODE_API_KEY,
                    "regions": "US"
                }
            )
            sources_response.raise_for_status()
            sources = sources_response.json()
            
            # Group by type: stream (subscription/free), rent, buy
            grouped = {"stream": [], "rent": [], "buy": []}
            seen_services = {"stream": set(), "rent": set(), "buy": set()}
            
            for source in sources:
                source_name = source.get("name", "")
                source_id = str(source.get("source_id", ""))
                source_type = source.get("type", "").lower()
                web_url = source.get("web_url", "")
                
                # Map type to our categories
                if source_type in ["sub", "free", "tve"]:
                    category = "stream"
                elif source_type == "rent":
                    category = "rent"
                elif source_type == "buy":
                    category = "buy"
                else:
                    continue
                
                # Avoid duplicates
                if source_id not in seen_services[category]:
                    grouped[category].append({
                        "name": source_name,
                        "id": source_id,
                        "link": web_url
                    })
                    seen_services[category].add(source_id)
            
            return grouped
        except Exception as e:
            logger.error(f"WatchMode API error: {str(e)}")
            return None

def calculate_hit_flop(budget: Optional[int], revenue: Optional[int]) -> str:
    """Calculate hit/flop status"""
    if not budget or not revenue or budget == 0:
        return "Unknown"
    
    ratio = revenue / budget
    if ratio >= 2.0:
        return "Hit"
    elif ratio < 1.0:
        return "Flop"
    else:
        return "Average"

def get_tmdb_sort_param(sort_by: Optional[str]) -> str:
    """Map frontend sort_by to TMDB sort_by parameter"""
    if not sort_by:
        return "popularity.desc"
    
    sort_map = {
        "rating_desc": "vote_average.desc",
        "rating_asc": "vote_average.asc",
        "year_desc": "primary_release_date.desc",
        "year_asc": "primary_release_date.asc"
    }
    
    return sort_map.get(sort_by, "popularity.desc")

def apply_manual_sort(results: List[Dict], sort_by: Optional[str]) -> List[Dict]:
    """Apply sorting to a list of results (for manual pagination)"""
    if not sort_by:
        # Default: sort by popularity
        results.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    elif sort_by == "rating_desc":
        results.sort(key=lambda x: x.get("vote_average", 0), reverse=True)
    elif sort_by == "rating_asc":
        results.sort(key=lambda x: x.get("vote_average", 0))
    elif sort_by == "year_desc":
        # Sort by release_date or first_air_date, putting items without dates at the end
        results.sort(key=lambda x: (x.get("release_date") or x.get("first_air_date") or "0000-00-00"), reverse=True)
    elif sort_by == "year_asc":
        # Sort by release_date or first_air_date, putting items without dates at the end
        results.sort(key=lambda x: (x.get("release_date") or x.get("first_air_date") or "9999-99-99"))
    
    return results

# ===== API Routes =====
@api_router.post("/search")
async def search_titles(request: SearchRequest):
    """Search for movies/TV shows with filters"""
    try:
        # Save to search history
        history_item = SearchHistoryItem(
            query=request.query, 
            scope=request.scope,
            genre=request.genre,
            language=request.language,
            content_type=request.content_type
        )
        await db.search_history.insert_one(history_item.dict())
        
        results = []
        needs_post_filtering = False  # Track if we need to apply filters after getting results
        
        if request.scope == SearchScope.TITLE:
            # Multi-search for titles
            search_params = {
                "query": request.query,
                "page": request.page,
                "include_adult": False
            }
            if request.language:
                search_params["language"] = request.language
            
            data = await fetch_tmdb_data("search/multi", search_params)
            results = data.get("results", [])
            total_pages = data.get("total_pages", 1)
            needs_post_filtering = True  # Title search needs post-filtering for genre/content_type
            
        elif request.scope == SearchScope.GENRE:
            # Search by genre - get genre ID first
            genres_movie = await fetch_tmdb_data("genre/movie/list")
            genres_tv = await fetch_tmdb_data("genre/tv/list")
            all_genres = genres_movie.get("genres", []) + genres_tv.get("genres", [])
            
            # Find matching genre
            matching_genre = next((g for g in all_genres if request.query.lower() in g["name"].lower()), None)
            
            if matching_genre:
                # Discover movies/TV with this genre
                discover_params = {
                    "with_genres": matching_genre["id"],
                    "page": request.page,
                    "sort_by": get_tmdb_sort_param(request.sort_by)
                }
                if request.language:
                    discover_params["with_original_language"] = request.language
                
                # Choose endpoint based on content_type
                if request.content_type == "tv":
                    endpoint = "discover/tv"
                else:
                    # Default to movies or use movie endpoint if content_type is "movie" or not specified
                    endpoint = "discover/movie"
                
                data = await fetch_tmdb_data(endpoint, discover_params)
                results = data.get("results", [])
                total_pages = data.get("total_pages", 1)
            else:
                results = []
                total_pages = 1
                
        elif request.scope == SearchScope.CAST:
            # Search for person first
            person_data = await fetch_tmdb_data("search/person", {
                "query": request.query,
                "page": 1
            })
            persons = person_data.get("results", [])
            
            if persons:
                # Select the most popular person with matching name
                persons.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                person_id = persons[0]["id"]
                logger.info(f"Selected person ID: {person_id} with popularity: {persons[0].get('popularity')}")
                
                # Use discover API if possible (only for movies), otherwise use combined_credits
                use_discover = request.genre and (not request.content_type or request.content_type == "movie")
                
                if use_discover:
                    # Use discover API with cast, genre, and language filters
                    discover_params = {
                        "with_cast": person_id,
                        "page": request.page,
                        "sort_by": get_tmdb_sort_param(request.sort_by)
                    }
                    if request.genre:
                        discover_params["with_genres"] = request.genre
                    if request.language:
                        discover_params["with_original_language"] = request.language
                    
                    data = await fetch_tmdb_data("discover/movie", discover_params)
                    results = data.get("results", [])
                    total_pages = data.get("total_pages", 1)
                else:
                    # Get all credits for this person and apply filters manually
                    credits = await fetch_tmdb_data(f"person/{person_id}/combined_credits")
                    cast_results = credits.get("cast", [])
                    
                    # Apply filters BEFORE sorting and pagination
                    filtered_results = []
                    for item in cast_results:
                        media_type = item.get("media_type", "movie")
                        if media_type not in ["movie", "tv"]:
                            continue
                        
                        # Filter by content type
                        if request.content_type:
                            if request.content_type == "movie" and media_type != "movie":
                                continue
                            elif request.content_type == "tv" and media_type != "tv":
                                continue
                        
                        # Filter by genre
                        if request.genre:
                            item_genres = item.get("genre_ids", [])
                            if int(request.genre) not in item_genres:
                                continue
                        
                        # Filter by language
                        if request.language:
                            item_language = item.get("original_language", "")
                            if item_language != request.language:
                                continue
                        
                        filtered_results.append(item)
                    
                    # Apply user's requested sort and paginate manually
                    filtered_results = apply_manual_sort(filtered_results, request.sort_by)
                    start_idx = (request.page - 1) * 20
                    end_idx = start_idx + 20
                    results = filtered_results[start_idx:end_idx]
                    total_pages = (len(filtered_results) + 19) // 20
            else:
                results = []
                total_pages = 1
                
        elif request.scope == SearchScope.DIRECTOR:
            # Search for person first
            person_data = await fetch_tmdb_data("search/person", {
                "query": request.query,
                "page": 1
            })
            persons = person_data.get("results", [])
            
            if persons:
                # Select the most popular person with matching name
                persons.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                person_id = persons[0]["id"]
                
                # Use discover API if possible (only for movies), otherwise use combined_credits
                use_discover = request.genre and (not request.content_type or request.content_type == "movie")
                
                if use_discover:
                    # Use discover API with director, genre, and language filters
                    discover_params = {
                        "with_crew": person_id,
                        "page": request.page,
                        "sort_by": get_tmdb_sort_param(request.sort_by)
                    }
                    if request.genre:
                        discover_params["with_genres"] = request.genre
                    if request.language:
                        discover_params["with_original_language"] = request.language
                    
                    data = await fetch_tmdb_data("discover/movie", discover_params)
                    results = data.get("results", [])
                    total_pages = data.get("total_pages", 1)
                else:
                    # Get crew credits and apply filters manually
                    credits = await fetch_tmdb_data(f"person/{person_id}/combined_credits")
                    crew_results = [c for c in credits.get("crew", []) if c.get("job") == "Director"]
                    
                    # Apply filters BEFORE sorting and pagination
                    filtered_results = []
                    for item in crew_results:
                        media_type = item.get("media_type", "movie")
                        if media_type not in ["movie", "tv"]:
                            continue
                        
                        # Filter by content type
                        if request.content_type:
                            if request.content_type == "movie" and media_type != "movie":
                                continue
                            elif request.content_type == "tv" and media_type != "tv":
                                continue
                        
                        # Filter by genre
                        if request.genre:
                            item_genres = item.get("genre_ids", [])
                            if int(request.genre) not in item_genres:
                                continue
                        
                        # Filter by language
                        if request.language:
                            item_language = item.get("original_language", "")
                            if item_language != request.language:
                                continue
                        
                        filtered_results.append(item)
                    
                    # Apply user's requested sort and paginate
                    filtered_results = apply_manual_sort(filtered_results, request.sort_by)
                    start_idx = (request.page - 1) * 20
                    end_idx = start_idx + 20
                    results = filtered_results[start_idx:end_idx]
                    total_pages = (len(filtered_results) + 19) // 20
            else:
                results = []
                total_pages = 1
        
        # Format results with IMDb ratings
        formatted_results = []
        for item in results:
            media_type = item.get("media_type", "movie")
            if media_type not in ["movie", "tv"]:
                continue
            
            # Apply post-filtering only if needed (for title search with additional filters)
            if needs_post_filtering:
                # Filter by content type if specified
                if request.content_type:
                    if request.content_type == "movie" and media_type != "movie":
                        continue
                    elif request.content_type == "tv" and media_type != "tv":
                        continue
                
                # Filter by genre if specified
                if request.genre:
                    item_genres = item.get("genre_ids", [])
                    if int(request.genre) not in item_genres:
                        continue
                
                # Filter by language if specified
                if request.language:
                    item_language = item.get("original_language", "")
                    if item_language != request.language:
                        continue
            
            # Get basic info
            title = item.get("title") or item.get("name", "")
            year = (item.get("release_date") or item.get("first_air_date", ""))[:4]
            tmdb_id = item.get("id")
            
            # Fetch IMDb rating for this result
            imdb_rating = item.get("vote_average", 0)  # Default to TMDB
            try:
                # Get external IDs to fetch IMDb ID
                external_ids_data = await fetch_tmdb_data(f"{media_type}/{tmdb_id}/external_ids")
                imdb_id = external_ids_data.get("imdb_id")
                
                if imdb_id:
                    # Fetch IMDb rating from OMDb
                    omdb_data = await fetch_omdb_data(imdb_id)
                    if omdb_data:
                        omdb_rating = omdb_data.get("imdbRating")
                        if omdb_rating and omdb_rating != "N/A":
                            imdb_rating = float(omdb_rating)
            except Exception as e:
                logger.error(f"Error fetching IMDb rating for {tmdb_id}: {str(e)}")
                # Continue with TMDB rating as fallback
            
            formatted_item = {
                "id": tmdb_id,
                "title": title,
                "year": year,
                "media_type": media_type,
                "poster_path": item.get("poster_path"),
                "genres": item.get("genre_ids", []),
                "vote_average": imdb_rating,
                "overview": item.get("overview", ""),
                "original_language": item.get("original_language", "")
            }
            formatted_results.append(formatted_item)
        
        # Note: Sorting is now handled at the source (TMDB Discover API or manual sort before pagination)
        # No need to re-sort here as it would break pagination consistency
        
        return {
            "results": formatted_results,
            "page": request.page,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/title/{tmdb_id}")
async def get_title_details(tmdb_id: int, media_type: str = Query("movie", regex="^(movie|tv)$")):
    """Get detailed information for a specific title"""
    try:
        # Fetch TMDB details
        endpoint = f"{media_type}/{tmdb_id}"
        tmdb_data = await fetch_tmdb_data(endpoint, {"append_to_response": "credits,external_ids"})
        
        # Get IMDb ID for OMDb
        imdb_id = tmdb_data.get("external_ids", {}).get("imdb_id")
        
        # Fetch OMDb data for additional ratings
        omdb_data = None
        if imdb_id:
            omdb_data = await fetch_omdb_data(imdb_id)
        
        # Build ratings object
        ratings = {
            "tmdb": tmdb_data.get("vote_average", 0),
            "imdb": tmdb_data.get("vote_average", 0),  # Default to TMDB, will be overridden by OMDb
            "imdb_votes": None,
            "rotten_tomatoes_critics": None,
            "rotten_tomatoes_audience": None,
            "metacritic": None,
            "google_users": None
        }
        
        # Extract ratings from OMDb
        if omdb_data:
            omdb_ratings = omdb_data.get("Ratings", [])
            for rating in omdb_ratings:
                source = rating.get("Source", "")
                value = rating.get("Value", "")
                
                if "Rotten Tomatoes" in source:
                    # Parse percentage
                    if "%" in value:
                        ratings["rotten_tomatoes_critics"] = int(value.replace("%", ""))
                elif "Metacritic" in source:
                    # Parse score out of 100
                    if "/" in value:
                        ratings["metacritic"] = int(value.split("/")[0])
            
            # Get IMDb rating and vote count from OMDb (more precise)
            imdb_rating = omdb_data.get("imdbRating")
            if imdb_rating and imdb_rating != "N/A":
                ratings["imdb"] = float(imdb_rating)
            
            imdb_votes = omdb_data.get("imdbVotes")
            if imdb_votes and imdb_votes != "N/A":
                # Remove commas and convert to string for display
                ratings["imdb_votes"] = imdb_votes
        
        # Build response
        title = tmdb_data.get("title") or tmdb_data.get("name", "")
        year = (tmdb_data.get("release_date") or tmdb_data.get("first_air_date", ""))[:4]
        
        result = {
            "id": tmdb_id,
            "title": title,
            "year": year,
            "media_type": media_type,
            "poster_path": tmdb_data.get("poster_path"),
            "backdrop_path": tmdb_data.get("backdrop_path"),
            "overview": tmdb_data.get("overview", ""),
            "genres": [g["name"] for g in tmdb_data.get("genres", [])],
            "ratings": ratings,
            "tagline": tmdb_data.get("tagline", ""),
            "original_language": tmdb_data.get("original_language", ""),
            "imdb_id": imdb_id
        }
        
        # Add movie-specific data
        if media_type == "movie":
            budget = tmdb_data.get("budget", 0)
            revenue = tmdb_data.get("revenue", 0)
            result["runtime"] = tmdb_data.get("runtime")
            result["budget"] = budget
            result["box_office"] = revenue
            result["hit_flop_status"] = calculate_hit_flop(budget, revenue)
        
        # Add TV-specific data
        else:
            result["seasons"] = tmdb_data.get("number_of_seasons", 0)
            result["episodes"] = tmdb_data.get("number_of_episodes", 0)
            episode_runtimes = tmdb_data.get("episode_run_time", [])
            
            # If episode_run_time is empty, try to fetch from first episode
            if not episode_runtimes:
                try:
                    season_data = await fetch_tmdb_data(f"tv/{tmdb_id}/season/1")
                    episodes = season_data.get("episodes", [])
                    if episodes:
                        # Calculate average runtime from first season
                        runtimes = [ep.get("runtime") for ep in episodes if ep.get("runtime")]
                        if runtimes:
                            result["episode_runtime"] = int(sum(runtimes) / len(runtimes))
                        else:
                            result["episode_runtime"] = None
                    else:
                        result["episode_runtime"] = None
                except Exception as e:
                    logger.error(f"Error fetching season data: {str(e)}")
                    result["episode_runtime"] = None
            else:
                result["episode_runtime"] = episode_runtimes[0]
        
        # Add cast and crew
        credits = tmdb_data.get("credits", {})
        cast = credits.get("cast", [])[:5]
        result["cast"] = [{"name": c.get("name"), "character": c.get("character")} for c in cast]
        
        crew = credits.get("crew", [])
        directors = [c["name"] for c in crew if c.get("job") == "Director"][:3]
        producers = [c["name"] for c in crew if c.get("job") == "Producer"][:3]
        
        result["directors"] = directors
        result["producers"] = producers
        result["production_companies"] = [pc.get("name") for pc in tmdb_data.get("production_companies", [])[:3]]
        
        return result
        
    except Exception as e:
        logger.error(f"Title details error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/streaming/{tmdb_id}")
async def get_streaming_availability(tmdb_id: int, media_type: str = Query("movie", regex="^(movie|tv)$")):
    """Get US streaming availability for a title"""
    try:
        streaming_data = await fetch_streaming_availability(tmdb_id, media_type)
        
        if not streaming_data:
            return {
                "available": False,
                "stream": [],
                "rent": [],
                "buy": []
            }
        
        return {
            "available": True,
            **streaming_data
        }
        
    except Exception as e:
        logger.error(f"Streaming availability error: {str(e)}")
        # Return gracefully even on error
        return {
            "available": False,
            "stream": [],
            "rent": [],
            "buy": [],
            "error": "Streaming availability temporarily unavailable"
        }

@api_router.get("/streaming/compare/{tmdb_id}")
async def compare_streaming_apis(tmdb_id: int, media_type: str = Query("movie", regex="^(movie|tv)$")):
    """Compare streaming data from both RapidAPI and WatchMode"""
    try:
        # Get IMDb ID first
        endpoint = f"{media_type}/{tmdb_id}"
        tmdb_data = await fetch_tmdb_data(endpoint, {"append_to_response": "external_ids"})
        imdb_id = tmdb_data.get("external_ids", {}).get("imdb_id")
        
        if not imdb_id:
            return {
                "error": "No IMDb ID found for this title",
                "rapidapi": None,
                "watchmode": None
            }
        
        # Fetch from both APIs simultaneously
        rapidapi_data = await fetch_streaming_availability(tmdb_id, media_type)
        watchmode_data = await fetch_watchmode_streaming(imdb_id)
        
        return {
            "title": tmdb_data.get("title") or tmdb_data.get("name"),
            "imdb_id": imdb_id,
            "rapidapi": {
                "available": rapidapi_data is not None,
                "data": rapidapi_data if rapidapi_data else {"stream": [], "rent": [], "buy": []}
            },
            "watchmode": {
                "available": watchmode_data is not None,
                "data": watchmode_data if watchmode_data else {"stream": [], "rent": [], "buy": []}
            }
        }
        
    except Exception as e:
        logger.error(f"Compare streaming error: {str(e)}")
        return {
            "error": str(e),
            "rapidapi": None,
            "watchmode": None
        }

@api_router.get("/popular")
async def get_popular_titles(page: int = 1):
    """Get popular/trending titles"""
    try:
        # Get trending movies and TV shows
        trending = await fetch_tmdb_data("trending/all/week", {"page": page})
        
        results = []
        for item in trending.get("results", []):
            media_type = item.get("media_type", "movie")
            if media_type not in ["movie", "tv"]:
                continue
            
            title = item.get("title") or item.get("name", "")
            year = (item.get("release_date") or item.get("first_air_date", ""))[:4]
            
            results.append({
                "id": item.get("id"),
                "title": title,
                "year": year,
                "media_type": media_type,
                "poster_path": item.get("poster_path"),
                "genres": item.get("genre_ids", []),
                "vote_average": item.get("vote_average", 0)
            })
        
        return {
            "results": results,
            "page": page,
            "total_pages": trending.get("total_pages", 1)
        }
        
    except Exception as e:
        logger.error(f"Popular titles error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/search/history")
async def get_search_history(limit: int = 10):
    """Get recent search history"""
    try:
        history = await db.search_history.find().sort("timestamp", -1).limit(limit).to_list(limit)
        return [SearchHistoryItem(**item) for item in history]
    except Exception as e:
        logger.error(f"Search history error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/search/history")
async def clear_search_history():
    """Clear search history"""
    try:
        await db.search_history.delete_many({})
        return {"message": "Search history cleared"}
    except Exception as e:
        logger.error(f"Clear history error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/genres")
async def get_genres():
    """Get all available genres"""
    try:
        movie_genres = await fetch_tmdb_data("genre/movie/list")
        tv_genres = await fetch_tmdb_data("genre/tv/list")
        
        # Combine and deduplicate
        all_genres = {}
        for g in movie_genres.get("genres", []) + tv_genres.get("genres", []):
            all_genres[g["id"]] = g["name"]
        
        return {"genres": all_genres}
    except Exception as e:
        logger.error(f"Genres error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@api_router.get("/")
async def root():
    return {"message": "Movie Recommendation API", "status": "running"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()