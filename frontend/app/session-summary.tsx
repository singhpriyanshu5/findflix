import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Image,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';
const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500';

interface Match {
  movie_id: number;
  media_type: string;
  movie_title: string;
  movie_poster?: string;
  matched_at: string;
}

interface SessionSummary {
  session_id: string;
  total_swipes: number;
  total_matches: number;
  matches: Match[];
  creator_swipes: number;
  friend_swipes: number;
}

export default function SessionSummaryScreen() {
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const params = useLocalSearchParams();
  const sessionId = params.sessionId as string;

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/auth');
      return;
    }
    
    loadSummary();
  }, [isAuthenticated, sessionId]);

  const loadSummary = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/swipe/summary/${sessionId}`);
      setSummary(response.data);
    } catch (error: any) {
      console.error('Failed to load summary:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const continueSwiping = () => {
    router.push({
      pathname: '/swipe-session',
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
          <Text style={styles.loadingText}>Loading matches...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!summary) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={64} color="#ef4444" />
          <Text style={styles.errorText}>Failed to load session summary</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadSummary}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header Stats */}
        <View style={styles.header}>
          <Text style={styles.title}>Your Matches</Text>
          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{summary.total_matches}</Text>
              <Text style={styles.statLabel}>Matches</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{summary.total_swipes}</Text>
              <Text style={styles.statLabel}>Total Swipes</Text>
            </View>
          </View>
        </View>

        {/* Matches List */}
        {summary.matches.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="heart-outline" size={64} color="#666" />
            <Text style={styles.emptyTitle}>No Matches Yet</Text>
            <Text style={styles.emptyText}>
              Keep swiping to find movies you both want to watch!
            </Text>
            <TouchableOpacity style={styles.continueButton} onPress={continueSwiping}>
              <Ionicons name="heart" size={20} color="#fff" />
              <Text style={styles.continueButtonText}>Continue Swiping</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.matchesSection}>
            <Text style={styles.sectionTitle}>
              Movies You Both Want to Watch ({summary.matches.length})
            </Text>
            
            {summary.matches.map((match, index) => (
              <View key={`${match.movie_id}-${index}`} style={styles.matchCard}>
                <View style={styles.matchPoster}>
                  {match.movie_poster ? (
                    <Image
                      source={{ uri: `${TMDB_IMAGE_BASE}${match.movie_poster}` }}
                      style={styles.posterImage}
                      resizeMode="cover"
                    />
                  ) : (
                    <View style={styles.placeholderPoster}>
                      <Ionicons name="film-outline" size={32} color="#666" />
                    </View>
                  )}
                </View>
                
                <View style={styles.matchInfo}>
                  <Text style={styles.matchTitle} numberOfLines={2}>
                    {match.movie_title}
                  </Text>
                  <View style={styles.matchMeta}>
                    <View style={styles.badge}>
                      <Text style={styles.badgeText}>
                        {match.media_type === 'movie' ? 'Movie' : 'TV Show'}
                      </Text>
                    </View>
                    <Text style={styles.matchDate}>
                      {new Date(match.matched_at).toLocaleDateString()}
                    </Text>
                  </View>
                </View>
                
                <View style={styles.matchAction}>
                  <View style={styles.heartIcon}>
                    <Ionicons name="heart" size={24} color="#e50914" />
                  </View>
                </View>
              </View>
            ))}

            {/* Continue Swiping Button */}
            <TouchableOpacity style={styles.continueButton} onPress={continueSwiping}>
              <Ionicons name="heart" size={20} color="#fff" />
              <Text style={styles.continueButtonText}>Continue Swiping</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  errorText: {
    color: '#fff',
    fontSize: 18,
    textAlign: 'center',
    marginVertical: 16,
  },
  retryButton: {
    backgroundColor: '#e50914',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    paddingVertical: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#e50914',
  },
  statLabel: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 64,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 16,
    color: '#888',
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 22,
  },
  matchesSection: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 16,
  },
  matchCard: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
  },
  matchPoster: {
    width: 60,
    height: 90,
    borderRadius: 8,
    overflow: 'hidden',
    marginRight: 16,
  },
  posterImage: {
    width: '100%',
    height: '100%',
  },
  placeholderPoster: {
    width: '100%',
    height: '100%',
    backgroundColor: '#2a2a2a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  matchInfo: {
    flex: 1,
  },
  matchTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
  },
  matchMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
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
  matchDate: {
    color: '#888',
    fontSize: 12,
  },
  matchAction: {
    marginLeft: 16,
  },
  heartIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(229, 9, 20, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  continueButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e50914',
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 24,
    gap: 8,
  },
  continueButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});