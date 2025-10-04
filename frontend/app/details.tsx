import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  Image,
  ScrollView,
  TouchableOpacity,
  Linking,
  Share,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { getLanguageName } from '../utils/languages';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';
const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500';
const { width } = Dimensions.get('window');

interface TitleDetails {
  id: number;
  title: string;
  year: string;
  media_type: string;
  poster_path: string | null;
  backdrop_path: string | null;
  overview: string;
  genres: string[];
  ratings: {
    tmdb: number;
    imdb: number;
    rotten_tomatoes_critics: number | null;
    rotten_tomatoes_audience: number | null;
    metacritic: number | null;
    google_users: number | null;
  };
  tagline: string;
  runtime?: number;
  budget?: number;
  box_office?: number;
  hit_flop_status?: string;
  seasons?: number;
  episodes?: number;
  episode_runtime?: number;
  cast: Array<{ name: string; character: string }>;
  directors: string[];
  producers: string[];
  production_companies: string[];
}

interface StreamingData {
  available: boolean;
  stream: Array<{ name: string; id: string; link: string }>;
  rent: Array<{ name: string; id: string; link: string }>;
  buy: Array<{ name: string; id: string; link: string }>;
  error?: string;
}

export default function DetailsScreen() {
  const params = useLocalSearchParams();
  const id = Number(params.id);
  const mediaType = params.mediaType as string;
  const [refreshKey, setRefreshKey] = useState(0);

  const { data: titleData, isLoading, refetch } = useQuery<TitleDetails>({
    queryKey: ['title', id, mediaType, refreshKey],
    queryFn: async () => {
      const response = await axios.get(
        `${BACKEND_URL}/api/title/${id}?media_type=${mediaType}`
      );
      return response.data;
    },
  });

  const { data: streamingData } = useQuery<StreamingData>({
    queryKey: ['streaming', id, mediaType, refreshKey],
    queryFn: async () => {
      const response = await axios.get(
        `${BACKEND_URL}/api/streaming/${id}?media_type=${mediaType}`
      );
      return response.data;
    },
  });

  const handleShare = async () => {
    if (titleData) {
      try {
        await Share.share({
          message: `Check out ${titleData.title} (${titleData.year})`,
        });
      } catch (error) {
        console.error('Share error:', error);
      }
    }
  };

  const handleProviderPress = async (link: string) => {
    if (link) {
      try {
        const supported = await Linking.canOpenURL(link);
        if (supported) {
          await Linking.openURL(link);
        }
      } catch (error) {
        console.error('Link error:', error);
      }
    }
  };

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const formatCurrency = (value: number) => {
    if (value >= 1000000000) {
      return `$${(value / 1000000000).toFixed(1)}B`;
    } else if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    return `$${value.toLocaleString()}`;
  };

  if (isLoading || !titleData) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#fff" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={false}
            onRefresh={handleRefresh}
            tintColor="#fff"
          />
        }
      >
        {/* Hero Section */}
        <View style={styles.hero}>
          {titleData.backdrop_path ? (
            <Image
              source={{ uri: `${TMDB_IMAGE_BASE}${titleData.backdrop_path}` }}
              style={styles.backdrop}
              resizeMode="cover"
            />
          ) : null}
          <View style={styles.heroContent}>
            <View style={styles.posterContainer}>
              {titleData.poster_path ? (
                <Image
                  source={{ uri: `${TMDB_IMAGE_BASE}${titleData.poster_path}` }}
                  style={styles.poster}
                  resizeMode="cover"
                />
              ) : (
                <View style={[styles.poster, styles.placeholderPoster]}>
                  <Ionicons name="film-outline" size={48} color="#666" />
                </View>
              )}
            </View>
            <View style={styles.heroInfo}>
              <Text style={styles.title}>{titleData.title}</Text>
              <View style={styles.metaRow}>
                {titleData.year && <Text style={styles.year}>{titleData.year}</Text>}
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>
                    {titleData.media_type === 'movie' ? 'Movie' : 'TV'}
                  </Text>
                </View>
                {titleData.hit_flop_status && (
                  <View
                    style={[
                      styles.badge,
                      titleData.hit_flop_status === 'Hit' && styles.badgeHit,
                      titleData.hit_flop_status === 'Flop' && styles.badgeFlop,
                    ]}
                  >
                    <Text style={styles.badgeText}>{titleData.hit_flop_status}</Text>
                  </View>
                )}
              </View>
              {titleData.genres && titleData.genres.length > 0 && (
                <View style={styles.genreRow}>
                  {titleData.genres.slice(0, 3).map((genre, idx) => (
                    genre && (
                      <Text key={idx} style={styles.genre}>
                        {genre}
                      </Text>
                    )
                  ))}
                </View>
              )}
              <TouchableOpacity style={styles.shareButton} onPress={handleShare}>
                <Ionicons name="share-outline" size={20} color="#fff" />
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Tagline */}
        {titleData.tagline && titleData.tagline.trim() !== '' && (
          <Text style={styles.tagline}>"{titleData.tagline}"</Text>
        )}

        {/* Overview */}
        {titleData.overview && titleData.overview.trim() !== '' && (
          <View style={styles.section}>
            <Text style={styles.overview}>{titleData.overview}</Text>
          </View>
        )}

        {/* Ratings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Ratings</Text>
          <View style={styles.ratingsGrid}>
            {titleData.ratings.tmdb > 0 && (
              <View style={styles.ratingCard}>
                <Text style={styles.ratingValue}>{titleData.ratings.tmdb.toFixed(1)}</Text>
                <Text style={styles.ratingLabel}>TMDB</Text>
              </View>
            )}
            {titleData.ratings.imdb > 0 && (
              <View style={styles.ratingCard}>
                <Text style={styles.ratingValue}>{titleData.ratings.imdb.toFixed(1)}</Text>
                <Text style={styles.ratingLabel}>IMDb</Text>
              </View>
            )}
            <View style={styles.ratingCard}>
              <Text style={styles.ratingValue}>
                {titleData.ratings.rotten_tomatoes_critics
                  ? `${titleData.ratings.rotten_tomatoes_critics}%`
                  : '—'}
              </Text>
              <Text style={styles.ratingLabel}>RT Critics</Text>
            </View>
            <View style={styles.ratingCard}>
              <Text style={styles.ratingValue}>
                {titleData.ratings.rotten_tomatoes_audience
                  ? `${titleData.ratings.rotten_tomatoes_audience}%`
                  : '—'}
              </Text>
              <Text style={styles.ratingLabel}>RT Audience</Text>
            </View>
            <View style={styles.ratingCard}>
              <Text style={styles.ratingValue}>
                {titleData.ratings.metacritic || '—'}
              </Text>
              <Text style={styles.ratingLabel}>Metacritic</Text>
            </View>
          </View>
        </View>

        {/* Streaming Availability */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Where to Watch (US)</Text>
          {streamingData?.error ? (
            <Text style={styles.errorText}>{streamingData.error}</Text>
          ) : streamingData?.available ? (
            <View>
              {streamingData.stream.length > 0 && (
                <View style={styles.providerGroup}>
                  <Text style={styles.providerGroupTitle}>Stream</Text>
                  <View style={styles.providerList}>
                    {streamingData.stream.map((provider) => (
                      <TouchableOpacity
                        key={provider.id}
                        style={styles.providerButton}
                        onPress={() => handleProviderPress(provider.link)}
                      >
                        <Text style={styles.providerName}>{provider.name}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}
              {streamingData.rent.length > 0 && (
                <View style={styles.providerGroup}>
                  <Text style={styles.providerGroupTitle}>Rent</Text>
                  <View style={styles.providerList}>
                    {streamingData.rent.map((provider) => (
                      <TouchableOpacity
                        key={provider.id}
                        style={styles.providerButton}
                        onPress={() => handleProviderPress(provider.link)}
                      >
                        <Text style={styles.providerName}>{provider.name}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}
              {streamingData.buy.length > 0 && (
                <View style={styles.providerGroup}>
                  <Text style={styles.providerGroupTitle}>Buy</Text>
                  <View style={styles.providerList}>
                    {streamingData.buy.map((provider) => (
                      <TouchableOpacity
                        key={provider.id}
                        style={styles.providerButton}
                        onPress={() => handleProviderPress(provider.link)}
                      >
                        <Text style={styles.providerName}>{provider.name}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}
            </View>
          ) : (
            <Text style={styles.notAvailableText}>
              No US streaming options available at this time
            </Text>
          )}
        </View>

        {/* Facts */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Facts</Text>
          {titleData.media_type === 'movie' ? (
            <View style={styles.factsList}>
              {titleData.runtime && (
                <View style={styles.factItem}>
                  <Ionicons name="time-outline" size={20} color="#888" />
                  <Text style={styles.factText}>{titleData.runtime} minutes</Text>
                </View>
              )}
              {titleData.budget && titleData.budget > 0 && (
                <View style={styles.factItem}>
                  <Ionicons name="cash-outline" size={20} color="#888" />
                  <Text style={styles.factText}>
                    Budget: {formatCurrency(titleData.budget)}
                  </Text>
                </View>
              )}
              {titleData.box_office && titleData.box_office > 0 && (
                <View style={styles.factItem}>
                  <Ionicons name="trending-up-outline" size={20} color="#888" />
                  <Text style={styles.factText}>
                    Box Office: {formatCurrency(titleData.box_office)}
                  </Text>
                </View>
              )}
            </View>
          ) : (
            <View style={styles.factsList}>
              {titleData.seasons && (
                <View style={styles.factItem}>
                  <Ionicons name="albums-outline" size={20} color="#888" />
                  <Text style={styles.factText}>{titleData.seasons} seasons</Text>
                </View>
              )}
              {titleData.episodes && (
                <View style={styles.factItem}>
                  <Ionicons name="list-outline" size={20} color="#888" />
                  <Text style={styles.factText}>{titleData.episodes} episodes</Text>
                </View>
              )}
              {titleData.episode_runtime && (
                <View style={styles.factItem}>
                  <Ionicons name="time-outline" size={20} color="#888" />
                  <Text style={styles.factText}>
                    ~{titleData.episode_runtime} min/episode
                  </Text>
                </View>
              )}
            </View>
          )}
        </View>

        {/* Cast & Crew */}
        {titleData.cast && titleData.cast.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Cast</Text>
            {titleData.cast.map((member, idx) => (
              <View key={idx} style={styles.castItem}>
                <Text style={styles.castName}>{member.name || 'Unknown'}</Text>
                <Text style={styles.castCharacter}>{member.character || 'Unknown role'}</Text>
              </View>
            ))}
          </View>
        )}

        {titleData.directors && titleData.directors.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Director(s)</Text>
            <Text style={styles.crewText}>{titleData.directors.join(', ')}</Text>
          </View>
        )}

        {titleData.producers && titleData.producers.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Producer(s)</Text>
            <Text style={styles.crewText}>{titleData.producers.join(', ')}</Text>
          </View>
        )}

        {titleData.production_companies && titleData.production_companies.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Production</Text>
            <Text style={styles.crewText}>
              {titleData.production_companies.join(', ')}
            </Text>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: {
    flex: 1,
  },
  hero: {
    height: 280,
    position: 'relative',
  },
  backdrop: {
    width: '100%',
    height: '100%',
    position: 'absolute',
    opacity: 0.3,
  },
  heroContent: {
    flex: 1,
    flexDirection: 'row',
    padding: 16,
    justifyContent: 'flex-start',
    alignItems: 'flex-end',
  },
  posterContainer: {
    marginRight: 16,
  },
  poster: {
    width: 120,
    height: 180,
    borderRadius: 8,
    backgroundColor: '#1a1a1a',
  },
  placeholderPoster: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  heroInfo: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  year: {
    fontSize: 16,
    color: '#aaa',
  },
  badge: {
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeHit: {
    backgroundColor: '#22c55e',
  },
  badgeFlop: {
    backgroundColor: '#ef4444',
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
  genreRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 8,
  },
  genre: {
    color: '#888',
    fontSize: 13,
  },
  shareButton: {
    marginTop: 8,
    padding: 8,
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  tagline: {
    fontSize: 16,
    fontStyle: 'italic',
    color: '#aaa',
    textAlign: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  section: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#1a1a1a',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  overview: {
    fontSize: 15,
    color: '#ccc',
    lineHeight: 22,
  },
  ratingsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  ratingCard: {
    flex: 1,
    minWidth: width / 2 - 26,
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  ratingValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  ratingLabel: {
    fontSize: 12,
    color: '#888',
  },
  providerGroup: {
    marginBottom: 16,
  },
  providerGroupTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#aaa',
    marginBottom: 8,
  },
  providerList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  providerButton: {
    backgroundColor: '#e50914',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  providerName: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  errorText: {
    color: '#888',
    fontSize: 14,
  },
  notAvailableText: {
    color: '#888',
    fontSize: 14,
  },
  factsList: {
    gap: 12,
  },
  factItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  factText: {
    fontSize: 15,
    color: '#ccc',
  },
  castItem: {
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a1a',
  },
  castName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 2,
  },
  castCharacter: {
    fontSize: 13,
    color: '#888',
  },
  crewText: {
    fontSize: 15,
    color: '#ccc',
    lineHeight: 22,
  },
});