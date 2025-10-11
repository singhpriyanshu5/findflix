import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

interface SearchHistoryItem {
  id: string;
  query: string;
  scope: string;
  genre?: string;
  language?: string;
  content_type?: string;
  timestamp: string;
}

export default function RecentSearchesScreen() {
  const [searches, setSearches] = useState<SearchHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/auth');
      return;
    }
    
    loadSearchHistory();
  }, [isAuthenticated]);

  const loadSearchHistory = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/search/history?limit=50`);
      setSearches(response.data);
    } catch (error) {
      console.error('Failed to load search history:', error);
      Alert.alert('Error', 'Failed to load search history');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchAgain = (search: SearchHistoryItem) => {
    // Navigate to index with search params
    const params: any = {
      query: search.query,
      scope: search.scope,
    };
    
    if (search.genre) params.genre = search.genre;
    if (search.language) params.language = search.language;
    if (search.content_type) params.content_type = search.content_type;
    
    router.push({
      pathname: '/',
      params,
    });
  };

  const handleClearHistory = () => {
    Alert.alert(
      'Clear Search History',
      'Are you sure you want to clear all search history?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.delete(`${BACKEND_URL}/api/search/history`);
              setSearches([]);
              Alert.alert('Success', 'Search history cleared');
            } catch (error) {
              Alert.alert('Error', 'Failed to clear search history');
            }
          },
        },
      ]
    );
  };

  const getScopeIcon = (scope: string) => {
    switch (scope) {
      case 'title':
        return 'film-outline';
      case 'cast':
        return 'person-outline';
      case 'director':
        return 'megaphone-outline';
      default:
        return 'search-outline';
    }
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const renderSearchItem = ({ item }: { item: SearchHistoryItem }) => (
    <TouchableOpacity
      style={styles.searchItem}
      onPress={() => handleSearchAgain(item)}
      activeOpacity={0.7}
    >
      <View style={styles.searchIcon}>
        <Ionicons name={getScopeIcon(item.scope) as any} size={20} color="#e50914" />
      </View>
      
      <View style={styles.searchContent}>
        <Text style={styles.searchQuery}>{item.query || 'Advanced Search'}</Text>
        <View style={styles.searchMeta}>
          <Text style={styles.scopeBadge}>{item.scope}</Text>
          {item.content_type && (
            <Text style={styles.metaText}>• {item.content_type}</Text>
          )}
          <Text style={styles.timeText}>• {formatDate(item.timestamp)}</Text>
        </View>
      </View>

      <Ionicons name="chevron-forward" size={20} color="#666" />
    </TouchableOpacity>
  );

  if (!isAuthenticated) {
    return null;
  }

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#fff" />
          <Text style={styles.loadingText}>Loading search history...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Recent Searches</Text>
        {searches.length > 0 && (
          <TouchableOpacity onPress={handleClearHistory}>
            <Text style={styles.clearButton}>Clear All</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Search List */}
      {searches.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="search-outline" size={64} color="#666" />
          <Text style={styles.emptyTitle}>No Recent Searches</Text>
          <Text style={styles.emptyText}>
            Your search history will appear here
          </Text>
          <TouchableOpacity
            style={styles.searchNowButton}
            onPress={() => router.push('/')}
          >
            <Text style={styles.searchNowText}>Start Searching</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={searches}
          renderItem={renderSearchItem}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContainer}
        />
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  clearButton: {
    color: '#e50914',
    fontSize: 14,
    fontWeight: '600',
  },
  listContainer: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  searchItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  searchIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(229, 9, 20, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  searchContent: {
    flex: 1,
  },
  searchQuery: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  searchMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  scopeBadge: {
    fontSize: 12,
    color: '#e50914',
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  metaText: {
    fontSize: 12,
    color: '#888',
    marginLeft: 4,
    textTransform: 'capitalize',
  },
  timeText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
    marginBottom: 24,
  },
  searchNowButton: {
    backgroundColor: '#e50914',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 24,
  },
  searchNowText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
