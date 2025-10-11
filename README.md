# FindFlix 🎬

**Find your next movie/tv show to watch - Now with Tinder-style matching!**

FindFlix is a comprehensive native mobile application built with React Native (Expo) that helps users discover movies and TV shows, view detailed information including ratings from multiple sources, find where to stream them in the US, and swipe through movies with friends to find perfect matches!

## ✨ Features

### 🎯 NEW: Tinder-Style Movie Matching
- **Swipe Sessions**: Create movie swipe sessions with friends
- **Social Discovery**: Swipe right on movies you like, left on ones you don't
- **Instant Matches**: See movies both you and your friends swiped right on
- **Friend System**: Add friends and create private swipe sessions
- **Session History**: View all your past sessions and matches
- **Smart Navigation**: Tap any matched movie to view full details

### 🔐 User Authentication
- **Email/Password Registration**: Secure JWT-based authentication with PBKDF2-HMAC-SHA256 password hashing
- **Login System**: 7-day session tokens with httpOnly cookies
- **Forgot Password**: Email-based password reset with secure tokens (requires SMTP configuration)
- **OAuth Integration**: Sign in with Google via Emergent Auth (optional)
- **Session Management**: Automatic cleanup of expired sessions
- **Secure Storage**: Password hashes stored separately from user data

### 🔍 Advanced Search & Discovery
- **Multi-scope Search**: Search by Title, Cast, or Director
- **Fuzzy Search**: Enhanced typo-tolerant search with smart corrections
  - Movie titles: "spidermn" → "spider-man"
  - Actor names: "leornardo dicapro" → "Leonardo DiCaprio"
  - Director names: "christopher nolen" → "Christopher Nolan"
- **Main Cast Filter**: Cast searches only show movies where actor is in top 15 billing
- **Empty Query Search**: Filter by genre/language without text input
- **Genre Filter**: 18 popular genres including Action, Comedy, Drama, Horror, Sci-Fi, and more
- **Language Filter**: 38+ languages including English, Hindi, Telugu, Tamil, Spanish, French, Japanese, Korean
- **Content Type Filter**: Filter by Movies only, TV Shows only, or All content
- **Smart Person Search**: Automatically selects the most popular person when searching by cast/director
- **Unreleased Tags**: Badges for upcoming movies not yet released
- **Search Results Caching**: 10-minute cache for stable navigation experience

### 📊 Comprehensive Ratings
- **TMDB Rating**: Community-driven ratings
- **IMDb Rating**: Industry-standard ratings with vote counts
- **Rotten Tomatoes**: Critics and Audience scores (when available)
- **Metacritic**: Aggregated critic reviews (when available)
- **Clickable IMDb**: Tap IMDb ratings to open the full IMDb page

### 🎯 Sorting Options
- Rating: High to Low / Low to High
- Release Year: Newest First / Oldest First
- Default: Popularity-based

### 📺 US Streaming Availability
- **Integrated APIs**: TMDB, WatchMode, and Streaming Availability API
- **Platforms Supported**: Netflix, Prime Video, Hulu, Disney+, HBO Max, Paramount+, Apple TV+, and 50+ more
- **Categorized Options**: Stream / Rent / Buy
- **Deep Links**: Direct links to streaming platforms

### 🎭 Rich Movie/TV Details
- **Trailer Player**: Watch movie/show trailers directly in the app (YouTube integration)
- **Hit/Flop Indicator**: Based on box office vs budget analysis
- **Movie Info**: Runtime, budget, box office revenue, production companies
- **TV Show Info**: Number of seasons, total episodes, average episode runtime
- **Cast & Crew**: Top 5 cast members with character names, directors, producers
- **Clickable Cast**: Tap any actor's name to see their entire filmography (newest first)
- **Original Language**: Display with icon in Facts section

### 📜 Smart Search History
- **User-Specific**: Each user's search history is private and saved automatically
- **Auto-Save**: Searches saved only for logged-in users (requires authentication)
- **Recent Searches Page**: Access from profile to view up to 50 recent searches
- **Filter Preservation**: Saves all filters (scope, genre, language, content type)
- **Visual Display**: Shows query, scope badge, content type, and relative timestamps
- **Quick Replay**: Tap any history item to re-run the exact same search
- **Clear History**: Delete all search history with one tap

### 👤 User Profile & Stats
- **Profile Page**: View account info and app statistics
- **Stats Dashboard**: 
  - Friends count
  - Pending invites (sent + received)
  - Total matches from swipe sessions
  - Total swipe sessions
- **Quick Actions**: Navigate to Movie Tinder, Add Friends, Recent Searches
- **Sign Out**: Secure logout with confirmation

### 🎬 Enhanced Swipe Experience
- **Real Swipe Gestures**: Drag cards left/right to swipe (20% threshold or quick flick)
- **Visual Feedback**: "LIKE" (green) and "NOPE" (red) indicators appear while swiping
- **Movie Trailers**: Auto-loading trailers on swipe cards (poster → trailer after 1.5s)
- **One-Tap Playback**: Tap YouTube play button to watch trailer
- **Pending Invites UI**: View sent/received friend requests on Tinder screen
- **Session Management**: Create, view, and end swipe sessions
- **Match Navigation**: Tap matched movies to view full details

### 🎨 Beautiful UI/UX
- **Dark Theme**: Eye-friendly dark mode
- **Native Feel**: Platform-specific optimizations for iOS and Android
- **Smooth Animations**: Polished transitions and interactions
- **Pull-to-Refresh**: Standard mobile gesture support
- **Infinite Scroll**: Seamless pagination on results

---

## 🛠 Tech Stack

### Frontend (Mobile)
- **Framework**: React Native with Expo SDK
- **Navigation**: Expo Router (file-based routing)
- **State Management**: TanStack React Query (server state)
- **UI Components**: React Native built-in components
- **Lists**: FlashList by Shopify (optimized performance)
- **Icons**: Expo Vector Icons (Ionicons)

### Backend (API)
- **Framework**: FastAPI (Python)
- **Database**: MongoDB (with Motor async driver)
- **HTTP Client**: httpx (async)
- **Validation**: Pydantic models

### External APIs
- **TMDB API**: Primary movie/TV data, cast/crew information, images
- **OMDb API**: IMDb ratings, vote counts, Rotten Tomatoes scores, Metacritic ratings
- **WatchMode API**: US streaming availability with deep links
- **Streaming Availability API (RapidAPI)**: Alternative streaming data source

---

## 📁 Project Structure

```
FindFlix/
├── backend/
│   ├── server.py              # FastAPI application with all endpoints
│   ├── auth_utils.py          # Authentication utilities and helpers
│   ├── models.py              # Pydantic models for user, session, friends, swipes
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Backend environment variables
├── frontend/
│   ├── app/
│   │   ├── _layout.tsx        # Root layout with navigation setup
│   │   ├── index.tsx          # Search screen (home)
│   │   ├── results.tsx        # Search results with sorting & caching
│   │   ├── details.tsx        # Movie/TV details with trailers & clickable cast
│   │   ├── auth.tsx           # Login/Register screen
│   │   ├── profile.tsx        # User profile with stats
│   │   ├── recent-searches.tsx # Search history page
│   │   ├── tinder.tsx         # Movie Tinder home (friends & sessions)
│   │   ├── add-friend.tsx     # Add friends by email
│   │   ├── create-session.tsx # Create swipe session
│   │   ├── swipe-session.tsx  # Swipe interface with trailers
│   │   └── session-summary.tsx # View matches from session
│   ├── contexts/
│   │   └── AuthContext.tsx    # Authentication context provider
│   ├── utils/
│   │   ├── languages.ts       # Language codes and utilities
│   │   └── genres.ts          # Genre IDs and utilities
│   ├── package.json           # Node dependencies
│   ├── app.json               # Expo configuration
│   └── .env                   # Frontend environment variables
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: v18+ and yarn
- **Python**: 3.9+
- **MongoDB**: Running locally or remote instance
- **Expo Go App**: For mobile testing (iOS/Android)

### API Keys Required
You'll need to obtain the following API keys (all have free tiers):

1. **TMDB API Key**
   - Sign up: https://www.themoviedb.org/signup
   - Get API key: Settings → API → Request API Key (Developer)
   - Free tier: Unlimited requests

2. **OMDb API Key**
   - Sign up: http://www.omdbapi.com/apikey.aspx
   - Select FREE tier (1,000 daily requests)
   - Check email for activation

3. **WatchMode API Key**
   - Request key: https://api.watchmode.com/requestApiKey
   - Free tier: 1,000 requests/month

4. **Streaming Availability API (RapidAPI)**
   - Sign up: https://rapidapi.com
   - Subscribe: https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability
   - Select "Basic" plan (FREE - 100 requests/day)

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/findflix.git
cd findflix
```

### 2. Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="findflix_db"
TMDB_API_KEY="your_tmdb_api_key"
RAPIDAPI_KEY="your_rapidapi_key"
OMDB_API_KEY="your_omdb_api_key"
WATCHMODE_API_KEY="your_watchmode_api_key"
EOF

# Start MongoDB (if local)
mongod --dbpath /path/to/data

# Run the backend server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Backend will be available at: `http://localhost:8001`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Create .env file (adjust URLs as needed)
cat > .env << EOF
EXPO_PUBLIC_BACKEND_URL=http://localhost:8001
EOF

# Start Expo development server
npx expo start
```

### 4. Run on Device

**Option A: Expo Go App (Recommended)**
1. Install Expo Go from App Store (iOS) or Play Store (Android)
2. Scan the QR code from terminal
3. App will load on your device

**Option B: Web Browser**
- Press `w` in terminal
- Opens in browser at `http://localhost:3000`

**Option C: iOS Simulator / Android Emulator**
- Press `i` for iOS simulator
- Press `a` for Android emulator

---

## 🔑 Environment Variables

### Backend (.env)
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="findflix_db"
TMDB_API_KEY="your_tmdb_api_key_here"
RAPIDAPI_KEY="your_rapidapi_key_here"
OMDB_API_KEY="your_omdb_api_key_here"
WATCHMODE_API_KEY="your_watchmode_api_key_here"

# Email Configuration (Optional - for password reset emails)
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USERNAME="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
FROM_EMAIL="your-email@gmail.com"
APP_URL="https://your-app-url.com"
```

### Frontend (.env)
```env
EXPO_PUBLIC_BACKEND_URL=http://your-backend-url:8001
```

**Note**: For mobile device testing with local backend, use your computer's IP address instead of `localhost`.

---

## 📧 Email Configuration (Optional)

The forgot password feature requires SMTP configuration to send password reset emails. Gmail is the easiest free option:

### Gmail Setup (Recommended - Free)

1. **Enable 2-Step Verification**
   - Go to https://myaccount.google.com/security
   - Turn on 2-Step Verification if not already enabled

2. **Generate App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Click "Generate"
   - Copy the 16-character password

3. **Update backend/.env**
   ```env
   SMTP_SERVER="smtp.gmail.com"
   SMTP_PORT="587"
   SMTP_USERNAME="your-email@gmail.com"
   SMTP_PASSWORD="your-16-char-app-password"
   FROM_EMAIL="your-email@gmail.com"
   APP_URL="http://localhost:3000"  # Your frontend URL
   ```

4. **Restart Backend**
   ```bash
   # Stop and restart the backend server to load new env variables
   uvicorn server:app --host 0.0.0.0 --port 8001 --reload
   ```

### Alternative: Brevo (formerly Sendinblue)
- Free tier: 300 emails/day
- Sign up: https://www.brevo.com/
- Get SMTP credentials from account settings
- Update `.env` with Brevo SMTP details

### Testing Email Sending
After configuration, test the forgot password flow:
1. Go to login screen
2. Click "Forgot Password?"
3. Enter registered email
4. Check inbox for reset email

**Note**: Without SMTP configuration, the forgot password feature will generate reset tokens but won't send emails.

---

## 📡 API Endpoints

### Authentication
```http
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/forgot-password
GET  /api/auth/me
POST /api/auth/oauth/session
```

### Friend System
```http
POST /api/friends/request        # Send friend request
GET  /api/friends/requests       # Get pending requests
POST /api/friends/respond        # Accept/decline request
GET  /api/friends                # Get friends list
```

### Swipe System
```http
GET  /api/swipe/session/{friend_id}    # Get/create swipe session
GET  /api/swipe/sessions               # Get all sessions
GET  /api/swipe/content/{session_id}   # Get movies to swipe
POST /api/swipe                        # Submit swipe
GET  /api/swipe/matches/{session_id}   # Get matches
GET  /api/swipe/summary/{session_id}   # Get session summary
POST /api/swipe/session/{session_id}/end
```

### Search
```http
POST /api/search
Content-Type: application/json

{
  "query": "Inception",
  "scope": "title",           // "title", "cast", or "director"
  "page": 1,
  "genre": "28",              // Optional: Genre ID
  "language": "en",           // Optional: ISO 639-1 code
  "content_type": "movie",    // Optional: "movie" or "tv"
  "sort_by": "rating_desc"    // Optional: "rating_desc", "rating_asc", "year_desc", "year_asc"
}
```

### Movie/TV Details
```http
GET /api/title/{tmdb_id}?media_type=movie
```

### Streaming Availability
```http
GET /api/streaming/{tmdb_id}?media_type=movie
```

### Popular Titles
```http
GET /api/popular?page=1
```

### Fuzzy Search
```http
GET /api/search/fuzzy?query=spidermn&media_type=multi&page=1
```

### Search History
```http
GET /api/search/history?limit=10
DELETE /api/search/history
```

### Genres
```http
GET /api/genres
```

---

## 🎨 Key Features Explained

### Smart Cast/Director Search
When searching for a person (cast or director), the app:
1. Searches TMDB for all people matching the name
2. Sorts by popularity to find the most well-known person
3. Returns their filmography

**Without Genre Filter:**
- Uses `person/{id}/combined_credits` API
- Returns all movies and TV shows they've worked on
- Includes guest appearances and minor roles

**With Genre Filter:**
- Uses `discover/movie` API with `with_cast` or `with_crew` parameter
- Filters by the selected genre
- More accurate results, faster response

### Genre Filtering Intelligence
- **Title Search**: Direct genre filter on search results
- **Cast/Director Search**: Uses TMDB Discover API for efficient filtering
- **Combined Filters**: All filters work together (genre + language + content type)

### Rating Aggregation
The app intelligently combines ratings from multiple sources:
1. Fetches TMDB data (includes basic rating)
2. Gets IMDb ID from TMDB external IDs
3. Calls OMDb API with IMDb ID to get:
   - Accurate IMDb rating (more precise than TMDB's copy)
   - Vote count for credibility
   - Rotten Tomatoes scores
   - Metacritic score
4. Displays all available ratings with "—" for missing data

### Streaming Availability Logic
Uses a fallback approach:
1. Primary: WatchMode API (better coverage, 1,000/month free)
2. Secondary: Streaming Availability API (100/day free)
3. Groups results by: Stream, Rent, Buy
4. Deduplicates providers to avoid showing the same service multiple times

---

## 🐛 Known Limitations

1. **TV Show Streaming**: Discover API only supports movies with cast/director + genre filtering. TV shows fall back to combined_credits without genre filtering when searching by cast/director.

2. **Rotten Tomatoes Coverage**: OMDb doesn't have RT scores for all titles, especially newer or less popular content.

3. **Streaming Data**: Some titles may not have US streaming info available in the APIs.

4. **API Rate Limits**: 
   - TMDB: Generous, rarely hit
   - OMDb: 1,000/day (can be exceeded with heavy usage)
   - WatchMode: 1,000/month
   - Streaming Availability: 100/day

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- **TMDB**: For comprehensive movie/TV data
- **OMDb**: For IMDb and Rotten Tomatoes ratings
- **WatchMode**: For US streaming availability data
- **Expo**: For excellent React Native development experience
- **FastAPI**: For modern, fast Python API framework

---

## 📧 Contact

For questions or suggestions, please open an issue on GitHub.

---

## 🎯 Recent Updates & Bug Fixes

### ✅ Implemented (Latest)
- **Tinder-Style Social Feature**: Swipe movies with friends and find matches
- **Complete Auth System**: Email/password registration, login, forgot password
- **Friend System**: Send/accept friend requests, manage friendships
- **Swipe Sessions**: Create collaborative movie discovery sessions
- **Enhanced Search**: Fuzzy search with typo tolerance
- **Improved Ratings**: IMDb/TMDB ratings with source labels
- **Better Pagination**: Server-side caching for consistent results
- **Unreleased Content**: Badges for upcoming movies
- **Session Navigation**: Tap matched movies to view full details

### 🐛 Fixed
- Search result pagination and sorting consistency
- Backend TMDB API caching for combined_credits
- Node.js version compatibility (deployment)
- Frontend icon loading for web builds
- TV show episode runtime handling
- Empty query search with filters
- Rating fallback logic (IMDb → TMDB)

### 🎯 Future Enhancements
- [ ] Personal watchlists and favorites
- [ ] AI-powered personalized recommendations
- [ ] Movie trailers integration
- [ ] Group chat in swipe sessions
- [ ] Advanced filters (certification, runtime range, release date)
- [ ] Offline mode with cached data
- [ ] Push notifications for new releases and matches
- [ ] Multi-language app interface
- [ ] Password reset page (currently generates token only)

---

**Built with ❤️ for movie and TV enthusiasts**
