import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  Image,
  Pressable,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { FlashList } from '@shopify/flash-list';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { getLanguageName } from '../utils/languages';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';
const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500';

interface SearchResult {
  id: number;
  title: string;
  year: string;
  media_type: string;
  poster_path: string | null;
  genres: number[];
  vote_average: number;
  overview: string;
  original_language: string;
}

export default function ResultsScreen() {
  const params = useLocalSearchParams();
  const router = useRouter();
  const [page, setPage] = useState(1);

  const query = params.query as string;
  const scope = params.scope as string;

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['search', query, scope, page],
    queryFn: async () => {
      const response = await axios.post(`${BACKEND_URL}/api/search`, {
        query,
        scope,
        page,
      });
      return response.data;
    },
    enabled: !!query,
  });

  const handleItemPress = (item: SearchResult) => {
    router.push({
      pathname: '/details',
      params: { id: item.id, mediaType: item.media_type },
    });
  };

  const loadMore = useCallback(() => {
    if (!isFetching && data?.total_pages && page < data.total_pages) {
      setPage((prev) => prev + 1);
    }
  }, [isFetching, data?.total_pages, page]);

  const renderItem = ({ item }: { item: SearchResult }) => (
    <Pressable
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
      onPress={() => handleItemPress(item)}
    >
      <View style={styles.cardContent}>
        {item.poster_path ? (
          <Image
            source={{ uri: `${TMDB_IMAGE_BASE}${item.poster_path}` }}
            style={styles.poster}
            resizeMode="cover"
          />
        ) : (
          <View style={[styles.poster, styles.placeholderPoster]}>
            <Ionicons name="film-outline" size={40} color="#666" />
          </View>
        )}

        <View style={styles.info}>
          <View style={styles.titleRow}>
            <Text style={styles.title} numberOfLines={2}>
              {item.title}
            </Text>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>
                {item.media_type === 'movie' ? 'Movie' : 'TV'}
              </Text>
            </View>
          </View>

          <View style={styles.metaRow}>
            <Text style={styles.year}>{item.year}</Text>
            {item.original_language && (
              <View style={styles.languageBadge}>
                <Text style={styles.languageBadgeText}>
                  {getLanguageName(item.original_language)}
                </Text>
              </View>
            )}
          </View>

          <Text style={styles.overview} numberOfLines={3}>
            {item.overview}
          </Text>

          {item.vote_average > 0 && (
            <View style={styles.ratingRow}>
              <Ionicons name="star" size={16} color="#ffd700" />
              <Text style={styles.ratingText}>
                {item.vote_average.toFixed(1)}
              </Text>
            </View>
          )}
        </View>
      </View>
    </Pressable>
  );

  const renderEmptyComponent = () => {
    if (isLoading) return null;
    return (
      <View style={styles.emptyContainer}>
        <Ionicons name="search-outline" size={64} color="#666" />
        <Text style={styles.emptyTitle}>No results found</Text>
        <Text style={styles.emptyText}>
          No matches for "{query}" in {scope}. Try a different filter.
        </Text>
      </View>
    );
  };

  const renderFooter = () => {
    if (!isFetching) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color="#fff" />
      </View>
    );
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#fff" />
          <Text style={styles.loadingText}>Searching...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <FlashList
        data={data?.results || []}
        renderItem={renderItem}
        keyExtractor={(item) => `${item.id}-${item.media_type}`}
        estimatedItemSize={150}
        onEndReached={loadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={renderFooter}
        ListEmptyComponent={renderEmptyComponent}
        refreshControl={
          <RefreshControl
            refreshing={false}
            onRefresh={() => {
              setPage(1);
              refetch();
            }}
            tintColor="#fff"
          />
        }
        contentContainerStyle={styles.listContent}
      />
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
  listContent: {
    paddingVertical: 8,
  },
  card: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
    overflow: 'hidden',
  },
  cardPressed: {
    opacity: 0.7,
  },
  cardContent: {
    flexDirection: 'row',
    padding: 12,
  },
  poster: {
    width: 100,
    height: 150,
    borderRadius: 8,
    backgroundColor: '#2a2a2a',
  },
  placeholderPoster: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  info: {
    flex: 1,
    marginLeft: 12,
    justifyContent: 'space-between',
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  title: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginRight: 8,
  },
  badge: {
    backgroundColor: '#e50914',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  year: {
    fontSize: 14,
    color: '#888',
  },
  languageBadge: {
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  languageBadgeText: {
    color: '#aaa',
    fontSize: 11,
    fontWeight: '600',
  },
  overview: {
    fontSize: 13,
    color: '#aaa',
    lineHeight: 18,
    marginBottom: 8,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  ratingText: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 64,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
    lineHeight: 20,
  },
  footerLoader: {
    paddingVertical: 16,
  },
});