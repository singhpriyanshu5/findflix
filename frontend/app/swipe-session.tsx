import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Image,
  Dimensions,
  Animated,
  PanResponder,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import YoutubePlayer from 'react-native-youtube-iframe';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';
const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500';
const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

interface Movie {
  id: number;
  title: string;
  year: string;
  media_type: string;
  poster_path?: string;
  backdrop_path?: string;
  overview: string;
  vote_average: number;
  genres: number[];
}

export default function SwipeSessionScreen() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSwipeLoading, setIsSwipeLoading] = useState(false);
  const [matches, setMatches] = useState<Movie[]>([]);
  const [showMatchModal, setShowMatchModal] = useState(false);
  const [matchedMovie, setMatchedMovie] = useState<Movie | null>(null);
  const [trailerKey, setTrailerKey] = useState<string | null>(null);
  const [showTrailer, setShowTrailer] = useState(false);
  const [isTrailerPlaying, setIsTrailerPlaying] = useState(false);
  const [playerReady, setPlayerReady] = useState(false);
  
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const params = useLocalSearchParams();
  const sessionId = params.sessionId as string;
  const posterTimerRef = useRef<NodeJS.Timeout | null>(null);
  const playTimerRef = useRef<NodeJS.Timeout | null>(null);
  const playerRef = useRef<any>(null);

  // Animation refs
  const swipeAnimation = useRef(new Animated.ValueXY()).current;
  const rotateAnimation = useRef(new Animated.Value(0)).current;
  const scaleAnimation = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/auth');
      return;
    }
    
    loadMovies();
  }, [isAuthenticated, sessionId]);

  // Load trailer when current movie changes
  useEffect(() => {
    if (movies.length > 0 && currentIndex < movies.length) {
      loadTrailerForCurrentMovie();
    }
    
    // Cleanup timer on unmount or index change
    return () => {
      if (posterTimerRef.current) {
        clearTimeout(posterTimerRef.current);
      }
      if (playTimerRef.current) {
        clearTimeout(playTimerRef.current);
      }
    };
  }, [currentIndex, movies]);

  const loadTrailerForCurrentMovie = async () => {
    // Reset trailer state
    setShowTrailer(false);
    setTrailerKey(null);
    setIsTrailerPlaying(false);
    setPlayerReady(false);
    
    // Clear any existing timers
    if (posterTimerRef.current) {
      clearTimeout(posterTimerRef.current);
    }
    if (playTimerRef.current) {
      clearTimeout(playTimerRef.current);
    }

    const currentMovie = movies[currentIndex];
    if (!currentMovie) return;

    try {
      // Fetch trailer
      const response = await axios.get(
        `${BACKEND_URL}/api/trailer/${currentMovie.id}?media_type=${currentMovie.media_type}`
      );
      
      if (response.data.trailer_key) {
        setTrailerKey(response.data.trailer_key);
        
        // Show poster for 1.5 seconds, then show trailer
        posterTimerRef.current = setTimeout(() => {
          console.log('Showing trailer');
          setShowTrailer(true);
        }, 1500);
      }
    } catch (error) {
      console.error('Failed to load trailer:', error);
      // Silently fail - just show poster
    }
  };

  const handlePlayerReady = () => {
    console.log('Player is ready, starting autoplay');
    setPlayerReady(true);
    setIsTrailerPlaying(true);
  };

  const loadMovies = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/swipe/content/${sessionId}`);
      setMovies(response.data.results);
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to load movies';
      Alert.alert('Error', message);
      router.goBack();
    } finally {
      setIsLoading(false);
    }
  };

  const submitSwipe = async (action: 'like' | 'dislike') => {
    if (currentIndex >= movies.length) return;
    
    const movie = movies[currentIndex];
    setIsSwipeLoading(true);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/swipe`, {
        session_id: sessionId,
        movie_id: movie.id,
        media_type: movie.media_type,
        action,
        movie_title: movie.title,
        movie_poster: movie.poster_path,
      });

      if (response.data.match_created) {
        setMatchedMovie(movie);
        setMatches(prev => [...prev, movie]);
        setShowMatchModal(true);
      }

      // Move to next movie
      setCurrentIndex(prev => prev + 1);
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to record swipe';
      Alert.alert('Error', message);
    } finally {
      setIsSwipeLoading(false);
    }
  };

  const resetAnimations = () => {
    swipeAnimation.setValue({ x: 0, y: 0 });
    rotateAnimation.setValue(0);
    scaleAnimation.setValue(1);
  };

  const animateSwipe = (direction: 'left' | 'right', callback?: () => void) => {
    const toValue = direction === 'left' ? -SCREEN_WIDTH : SCREEN_WIDTH;
    
    Animated.parallel([
      Animated.timing(swipeAnimation.x, {
        toValue,
        duration: 300,
        useNativeDriver: false,
      }),
      Animated.timing(rotateAnimation, {
        toValue: direction === 'left' ? -30 : 30,
        duration: 300,
        useNativeDriver: false,
      }),
    ]).start(() => {
      resetAnimations();
      callback?.();
    });
  };

  const handleLike = () => {
    animateSwipe('right', () => submitSwipe('like'));
  };

  const handleDislike = () => {
    animateSwipe('left', () => submitSwipe('dislike'));
  };

  // Pan responder for swipe gestures
  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (evt, gestureState) => {
        return Math.abs(gestureState.dx) > 20 || Math.abs(gestureState.dy) > 20;
      },
      
      onPanResponderMove: (evt, gestureState) => {
        swipeAnimation.setValue({ x: gestureState.dx, y: 0 });
        
        // Rotate based on horizontal movement
        const rotation = gestureState.dx / SCREEN_WIDTH * 30;
        rotateAnimation.setValue(rotation);
      },
      
      onPanResponderRelease: (evt, gestureState) => {
        const threshold = SCREEN_WIDTH * 0.25;
        
        if (gestureState.dx > threshold) {
          // Swipe right (like)
          animateSwipe('right', () => submitSwipe('like'));
        } else if (gestureState.dx < -threshold) {
          // Swipe left (dislike)
          animateSwipe('left', () => submitSwipe('dislike'));
        } else {
          // Snap back
          Animated.parallel([
            Animated.spring(swipeAnimation.x, {
              toValue: 0,
              useNativeDriver: false,
            }),
            Animated.spring(rotateAnimation, {
              toValue: 0,
              useNativeDriver: false,
            }),
          ]).start();
        }
      },
    })
  ).current;

  const viewMatches = () => {
    router.push({
      pathname: '/session-summary',
      params: { sessionId },
    });
  };

  if (!isAuthenticated) {
    return null;
  }

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#fff" />
          <Text style={styles.loadingText}>Loading movies...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (currentIndex >= movies.length) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.completedContainer}>
          <Ionicons name="checkmark-circle-outline" size={80} color="#22c55e" />
          <Text style={styles.completedTitle}>Session Complete!</Text>
          <Text style={styles.completedText}>
            You've swiped through all available movies.
          </Text>
          <Text style={styles.matchesText}>
            You have {matches.length} matches!
          </Text>
          <TouchableOpacity style={styles.viewMatchesButton} onPress={viewMatches}>
            <Text style={styles.viewMatchesButtonText}>View Matches</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const currentMovie = movies[currentIndex];
  const progress = ((currentIndex + 1) / movies.length) * 100;

  const rotateInterpolate = rotateAnimation.interpolate({
    inputRange: [-30, 0, 30],
    outputRange: ['-30deg', '0deg', '30deg'],
  });

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${progress}%` }]} />
          </View>
          <Text style={styles.progressText}>
            {currentIndex + 1} / {movies.length}
          </Text>
        </View>
        <TouchableOpacity style={styles.matchesButton} onPress={viewMatches}>
          <Ionicons name="heart" size={20} color="#e50914" />
          <Text style={styles.matchesButtonText}>{matches.length}</Text>
        </TouchableOpacity>
      </View>

      {/* Movie Card */}
      <View style={styles.cardContainer}>
        <Animated.View
          style={[
            styles.card,
            {
              transform: [
                { translateX: swipeAnimation.x },
                { translateY: swipeAnimation.y },
                { rotate: rotateInterpolate },
                { scale: scaleAnimation },
              ],
            },
          ]}
          {...panResponder.panHandlers}
        >
          {/* Show trailer if available and ready, otherwise show poster */}
          {showTrailer && trailerKey ? (
            <View style={styles.trailerContainer}>
              <YoutubePlayer
                key={`${trailerKey}-${currentIndex}`}
                height={SCREEN_HEIGHT * 0.6}
                play={true}
                videoId={trailerKey}
                onChangeState={(state) => {
                  console.log('Video state:', state);
                }}
                initialPlayerParams={{
                  controls: 1,
                  modestbranding: 1,
                  rel: 0,
                  loop: 0,
                }}
                mute={true}
                forceAndroidAutoplay={true}
                allowWebViewZoom={false}
                webViewStyle={{
                  opacity: 0.99,
                }}
                webViewProps={{
                  allowsInlineMediaPlayback: true,
                  mediaPlaybackRequiresUserAction: false,
                  javaScriptEnabled: true,
                  domStorageEnabled: true,
                }}
              />
            </View>
          ) : (
            <>
              {currentMovie.poster_path ? (
                <Image
                  source={{ uri: `${TMDB_IMAGE_BASE}${currentMovie.poster_path}` }}
                  style={styles.moviePoster}
                  resizeMode="cover"
                />
              ) : (
                <View style={[styles.moviePoster, styles.placeholderPoster]}>
                  <Ionicons name="film-outline" size={64} color="#666" />
                </View>
              )}
            </>
          )}
          
          <View style={styles.movieInfo}>
            <View style={styles.titleRow}>
              <Text style={styles.movieTitle} numberOfLines={2}>
                {currentMovie.title}
              </Text>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>
                  {currentMovie.media_type === 'movie' ? 'Movie' : 'TV'}
                </Text>
              </View>
            </View>
            
            <View style={styles.metaRow}>
              <Text style={styles.movieYear}>{currentMovie.year}</Text>
              {currentMovie.vote_average > 0 && (
                <View style={styles.ratingContainer}>
                  <Ionicons name="star" size={14} color="#ffd700" />
                  <Text style={styles.rating}>
                    {currentMovie.vote_average.toFixed(1)}
                  </Text>
                </View>
              )}
            </View>
            
            <Text style={styles.movieOverview} numberOfLines={3}>
              {currentMovie.overview}
            </Text>
          </View>
        </Animated.View>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionContainer}>
        <TouchableOpacity
          style={[styles.actionButton, styles.dislikeButton]}
          onPress={handleDislike}
          disabled={isSwipeLoading}
        >
          <Ionicons name="close" size={32} color="#fff" />
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.actionButton, styles.likeButton]}
          onPress={handleLike}
          disabled={isSwipeLoading}
        >
          <Ionicons name="heart" size={32} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Match Modal */}
      {showMatchModal && matchedMovie && (
        <View style={styles.matchModal}>
          <View style={styles.matchContent}>
            <Text style={styles.matchTitle}>It's a Match! 🎉</Text>
            <Image
              source={{ uri: `${TMDB_IMAGE_BASE}${matchedMovie.poster_path}` }}
              style={styles.matchPoster}
              resizeMode="cover"
            />
            <Text style={styles.matchMovieTitle}>{matchedMovie.title}</Text>
            <Text style={styles.matchText}>
              You both want to watch this!
            </Text>
            <TouchableOpacity
              style={styles.matchButton}
              onPress={() => setShowMatchModal(false)}
            >
              <Text style={styles.matchButtonText}>Keep Swiping</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
      
      {isSwipeLoading && (
        <View style={styles.swipeLoader}>
          <ActivityIndicator size="large" color="#fff" />
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#888',
    fontSize: 16,
    marginTop: 16,
  },
  completedContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  completedTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 24,
    marginBottom: 12,
  },
  completedText: {
    fontSize: 16,
    color: '#888',
    textAlign: 'center',
    marginBottom: 16,
  },
  matchesText: {
    fontSize: 18,
    color: '#e50914',
    fontWeight: '600',
    marginBottom: 32,
  },
  viewMatchesButton: {
    backgroundColor: '#e50914',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  viewMatchesButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  progressContainer: {
    flex: 1,
    marginRight: 16,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#2a2a2a',
    borderRadius: 2,
    marginBottom: 4,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#e50914',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: '#888',
  },
  matchesButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 20,
    gap: 4,
  },
  matchesButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  cardContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  card: {
    width: SCREEN_WIDTH - 48,
    height: SCREEN_HEIGHT * 0.7,
    backgroundColor: '#1a1a1a',
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  moviePoster: {
    width: '100%',
    height: '70%',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    backgroundColor: '#2a2a2a',
  },
  placeholderPoster: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  trailerContainer: {
    width: '100%',
    height: '70%',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    backgroundColor: '#000',
    overflow: 'hidden',
    position: 'relative',
  },
  muteIndicator: {
    position: 'absolute',
    bottom: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 4,
  },
  muteText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '500',
  },
  movieInfo: {
    flex: 1,
    padding: 20,
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  movieTitle: {
    flex: 1,
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginRight: 12,
  },
  badge: {
    backgroundColor: '#e50914',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '600',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 16,
  },
  movieYear: {
    fontSize: 16,
    color: '#888',
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  rating: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '600',
  },
  movieOverview: {
    fontSize: 14,
    color: '#ccc',
    lineHeight: 20,
  },
  actionContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingVertical: 32,
    paddingHorizontal: 24,
    gap: 80,
  },
  actionButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 4,
  },
  dislikeButton: {
    backgroundColor: '#ef4444',
  },
  likeButton: {
    backgroundColor: '#22c55e',
  },
  matchModal: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.9)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  matchContent: {
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  matchTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 32,
  },
  matchPoster: {
    width: 150,
    height: 225,
    borderRadius: 12,
    marginBottom: 16,
  },
  matchMovieTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
    textAlign: 'center',
  },
  matchText: {
    fontSize: 16,
    color: '#888',
    marginBottom: 32,
    textAlign: 'center',
  },
  matchButton: {
    backgroundColor: '#e50914',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  matchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  swipeLoader: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
  },
});