import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Pressable,
  ActivityIndicator,
  Image,
  RefreshControl,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { POPULAR_LANGUAGES, getLanguageName } from '../utils/languages';
import { POPULAR_GENRES, getGenreName } from '../utils/genres';
import { useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';
const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500';

type SearchScope = 'title' | 'cast' | 'director';

interface SearchHistoryItem {
  id: string;
  query: string;
  scope: SearchScope;
  genre: string | null;
  language: string | null;
  content_type: string | null;
  timestamp: string;
}

interface PopularTitle {
  id: number;
  title: string;
  year: string;
  media_type: string;
  poster_path: string | null;
  vote_average: number;
}

export default function SearchScreen() {
  const [searchMode, setSearchMode] = useState<'search' | 'ai'>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedScope, setSelectedScope] = useState<SearchScope>('title');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [selectedContentType, setSelectedContentType] = useState('');
  const [showGenreModal, setShowGenreModal] = useState(false);
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [showContentTypeModal, setShowContentTypeModal] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isAuthenticated, user, logout } = useAuth();

  // Fetch search history
  const { data: searchHistory, refetch: refetchHistory } = useQuery<SearchHistoryItem[]>({
    queryKey: ['searchHistory'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/search/history?limit=5`);
      return response.data;
    },
  });

  // Refetch search history when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      refetchHistory();
    }, [refetchHistory])
  );

  // Fetch popular titles
  const { data: popularData, isLoading: popularLoading, refetch } = useQuery({
    queryKey: ['popular'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/popular`);
      return response.data;
    },
  });

  // Clear history mutation
  const clearHistoryMutation = useMutation({
    mutationFn: async () => {
      await axios.delete(`${BACKEND_URL}/api/search/history`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['searchHistory'] });
    },
  });

  const handleSearch = () => {
    if (searchQuery.trim()) {
      router.push({
        pathname: '/results',
        params: { 
          query: searchQuery, 
          scope: selectedScope,
          genre: selectedGenre,
          language: selectedLanguage,
          contentType: selectedContentType
        },
      });
    }
  };

  const handleHistoryItemClick = (item: SearchHistoryItem) => {
    router.push({
      pathname: '/results',
      params: { 
        query: item.query, 
        scope: item.scope,
        genre: item.genre || '',
        language: item.language || '',
        contentType: item.content_type || ''
      },
    });
  };

  const handlePopularItemClick = (item: PopularTitle) => {
    router.push({
      pathname: '/details',
      params: { id: item.id, mediaType: item.media_type },
    });
  };

  const scopes: SearchScope[] = ['title', 'cast', 'director'];
  const selectedLanguageObj = POPULAR_LANGUAGES.find(l => l.code === selectedLanguage);
  const selectedGenreObj = POPULAR_GENRES.find(g => g.id === selectedGenre);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={popularLoading}
            onRefresh={() => refetch()}
            tintColor="#fff"
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <Text style={styles.title}>FindFlix</Text>
            <Text style={styles.subtitle}>Find your next movie/tv show to watch</Text>
          </View>
          <View style={styles.headerRight}>
            {isAuthenticated ? (
              <View style={styles.userSection}>
                <TouchableOpacity
                  style={styles.tinderButton}
                  onPress={() => router.push('/tinder')}
                >
                  <Ionicons name="heart" size={20} color="#fff" />
                  <Text style={styles.tinderButtonText}>Tinder</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.profileButton}
                  onPress={() => router.push('/profile')}
                >
                  <Text style={styles.profileButtonText}>
                    {user?.name.charAt(0).toUpperCase()}
                  </Text>
                </TouchableOpacity>
              </View>
            ) : (
              <TouchableOpacity
                style={styles.loginButton}
                onPress={() => router.push('/auth')}
              >
                <Text style={styles.loginButtonText}>Sign In</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
        {/* Mode Selector */}
        <View style={styles.modeSelector}>
          <TouchableOpacity
            style={[styles.modeButton, searchMode === 'search' && styles.modeButtonActive]}
            onPress={() => setSearchMode('search')}
            activeOpacity={0.7}
          >
            <Ionicons 
              name="search" 
              size={18} 
              color={searchMode === 'search' ? '#fff' : '#888'} 
              style={{marginRight: 8}}
            />
            <Text style={[styles.modeButtonText, searchMode === 'search' && styles.modeButtonTextActive]}>
              Movie Search
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeButton, searchMode === 'ai' && styles.modeButtonActive]}
            onPress={() => {
              if (!isAuthenticated) {
                router.push('/auth');
                return;
              }
              router.push('/ai-recommendations');
            }}
            activeOpacity={0.7}
          >
            <Ionicons 
              name="sparkles" 
              size={18} 
              color={searchMode === 'ai' ? '#fff' : '#888'} 
              style={{marginRight: 8}}
            />
            <Text style={[styles.modeButtonText, searchMode === 'ai' && styles.modeButtonTextActive]}>
              AI Recommendations
            </Text>
          </TouchableOpacity>
        </View>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <View style={styles.searchInputContainer}>
            <Ionicons name="search" size={20} color="#888" style={styles.searchIcon} />
            <TextInput
              style={styles.searchInput}
              placeholder="Search for movies, shows, people..."
              placeholderTextColor="#666"
              value={searchQuery}
              onChangeText={setSearchQuery}
              onSubmitEditing={handleSearch}
              returnKeyType="search"
            />
            {searchQuery.length > 0 && (
              <TouchableOpacity onPress={() => setSearchQuery('')}>
                <Ionicons name="close-circle" size={20} color="#888" />
              </TouchableOpacity>
            )}
          </View>

          {/* Filter Tabs */}
          <View style={styles.filterTabs}>
            {scopes.map((scope) => (
              <TouchableOpacity
                key={scope}
                style={[
                  styles.filterTab,
                  selectedScope === scope && styles.filterTabActive,
                ]}
                onPress={() => setSelectedScope(scope)}
              >
                <Text
                  style={[
                    styles.filterTabText,
                    selectedScope === scope && styles.filterTabTextActive,
                  ]}
                >
                  {scope.charAt(0).toUpperCase() + scope.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Genre Selector */}
          <TouchableOpacity
            style={styles.languageSelector}
            onPress={() => setShowGenreModal(true)}
          >
            <Ionicons name="film-outline" size={20} color="#fff" />
            <Text style={styles.languageSelectorText}>
              {selectedGenreObj?.name || 'All Genres'}
            </Text>
            <Ionicons name="chevron-down" size={16} color="#888" />
          </TouchableOpacity>

          {/* Language Selector */}
          <TouchableOpacity
            style={styles.languageSelector}
            onPress={() => setShowLanguageModal(true)}
          >
            <Ionicons name="language-outline" size={20} color="#fff" />
            <Text style={styles.languageSelectorText}>
              {selectedLanguageObj?.name || 'All Languages'}
            </Text>
            <Ionicons name="chevron-down" size={16} color="#888" />
          </TouchableOpacity>

          {/* Content Type Selector */}
          <TouchableOpacity
            style={styles.languageSelector}
            onPress={() => setShowContentTypeModal(true)}
          >
            <Ionicons name="film-outline" size={20} color="#fff" />
            <Text style={styles.languageSelectorText}>
              {selectedContentType === 'movie' ? 'Movies' : selectedContentType === 'tv' ? 'TV Shows' : 'All Content'}
            </Text>
            <Ionicons name="chevron-down" size={16} color="#888" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.searchButton}
            onPress={handleSearch}
            disabled={!searchQuery.trim()}
          >
            <Text style={styles.searchButtonText}>Search</Text>
          </TouchableOpacity>
        </View>

        {/* Recent Searches */}
        {searchHistory && searchHistory.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Recent Searches</Text>
              <TouchableOpacity onPress={() => clearHistoryMutation.mutate()}>
                <Text style={styles.clearButton}>Clear</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.historyList}>
              {searchHistory.map((item) => (
                <TouchableOpacity
                  key={item.id}
                  style={styles.historyItem}
                  onPress={() => handleHistoryItemClick(item)}
                >
                  <Ionicons name="time-outline" size={16} color="#888" />
                  <Text style={styles.historyText} numberOfLines={1}>
                    {item.query}
                  </Text>
                  <View style={styles.historyTags}>
                    <Text style={styles.historyScopeTag}>{item.scope}</Text>
                    {item.genre && (
                      <Text style={styles.historyGenreTag}>
                        {getGenreName(item.genre)}
                      </Text>
                    )}
                    {item.language && (
                      <Text style={styles.historyLanguageTag}>
                        {getLanguageName(item.language)}
                      </Text>
                    )}
                    {item.content_type && (
                      <Text style={styles.historyContentTypeTag}>
                        {item.content_type === 'movie' ? 'Movies' : 'TV'}
                      </Text>
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* Popular Picks */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Popular Now</Text>
          {popularLoading ? (
            <ActivityIndicator size="large" color="#fff" style={styles.loader} />
          ) : (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.popularGrid}>
              {popularData?.results?.slice(0, 10).map((item: PopularTitle) => (
                <Pressable
                  key={item.id}
                  style={styles.popularCard}
                  onPress={() => handlePopularItemClick(item)}
                >
                  {item.poster_path ? (
                    <Image
                      source={{ uri: `${TMDB_IMAGE_BASE}${item.poster_path}` }}
                      style={styles.popularPoster}
                      resizeMode="cover"
                    />
                  ) : (
                    <View style={[styles.popularPoster, styles.placeholderPoster]}>
                      <Ionicons name="film-outline" size={32} color="#666" />
                    </View>
                  )}
                  <View style={styles.popularInfo}>
                    <Text style={styles.popularTitle} numberOfLines={2}>
                      {item.title}
                    </Text>
                    <Text style={styles.popularYear}>{item.year}</Text>
                  </View>
                </Pressable>
              ))}
            </ScrollView>
          )}
        </View>
      </ScrollView>

      {/* Language Selection Modal */}
      <Modal
        visible={showLanguageModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowLanguageModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Language</Text>
              <TouchableOpacity onPress={() => setShowLanguageModal(false)}>
                <Ionicons name="close" size={24} color="#fff" />
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.modalScroll}>
              {POPULAR_LANGUAGES.map((lang) => (
                <TouchableOpacity
                  key={lang.code}
                  style={[
                    styles.languageOption,
                    selectedLanguage === lang.code && styles.languageOptionActive,
                  ]}
                  onPress={() => {
                    setSelectedLanguage(lang.code);
                    setShowLanguageModal(false);
                  }}
                >
                  <Text style={styles.languageOptionText}>{lang.name}</Text>
                  {selectedLanguage === lang.code && (
                    <Ionicons name="checkmark" size={20} color="#e50914" />
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Content Type Selection Modal */}
      <Modal
        visible={showContentTypeModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowContentTypeModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Content Type</Text>
              <TouchableOpacity onPress={() => setShowContentTypeModal(false)}>
                <Ionicons name="close" size={24} color="#fff" />
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.modalScroll}>
              {[
                { value: '', label: 'All Content' },
                { value: 'movie', label: 'Movies' },
                { value: 'tv', label: 'TV Shows' },
              ].map((type) => (
                <TouchableOpacity
                  key={type.value}
                  style={[
                    styles.languageOption,
                    selectedContentType === type.value && styles.languageOptionActive,
                  ]}
                  onPress={() => {
                    setSelectedContentType(type.value);
                    setShowContentTypeModal(false);
                  }}
                >
                  <Text style={styles.languageOptionText}>{type.label}</Text>
                  {selectedContentType === type.value && (
                    <Ionicons name="checkmark" size={20} color="#e50914" />
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Genre Selection Modal */}
      <Modal
        visible={showGenreModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowGenreModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Genre</Text>
              <TouchableOpacity onPress={() => setShowGenreModal(false)}>
                <Ionicons name="close" size={24} color="#fff" />
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.modalScroll}>
              {POPULAR_GENRES.map((genre) => (
                <TouchableOpacity
                  key={genre.id}
                  style={[
                    styles.languageOption,
                    selectedGenre === genre.id && styles.languageOptionActive,
                  ]}
                  onPress={() => {
                    setSelectedGenre(genre.id);
                    setShowGenreModal(false);
                  }}
                >
                  <Text style={styles.languageOptionText}>{genre.name}</Text>
                  {selectedGenre === genre.id && (
                    <Ionicons name="checkmark" size={20} color="#e50914" />
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>
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
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 24,
  },
  headerLeft: {
    flex: 1,
  },
  headerRight: {
    marginLeft: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#888',
  },
  userSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  tinderButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e50914',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 20,
    gap: 4,
  },
  tinderButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  profileButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#2a2a2a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  loginButton: {
    backgroundColor: '#1a1a1a',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  loginButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  searchContainer: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 12,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    color: '#fff',
    fontSize: 16,
  },
  filterTabs: {
    flexDirection: 'row',
    marginBottom: 12,
    gap: 8,
  },
  filterTab: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#1a1a1a',
    alignItems: 'center',
  },
  filterTabActive: {
    backgroundColor: '#e50914',
  },
  filterTabText: {
    color: '#888',
    fontSize: 14,
    fontWeight: '600',
  },
  filterTabTextActive: {
    color: '#fff',
  },
  languageSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 12,
    gap: 8,
  },
  languageSelectorText: {
    flex: 1,
    color: '#fff',
    fontSize: 15,
  },
  searchButton: {
    backgroundColor: '#e50914',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  section: {
    paddingHorizontal: 16,
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  clearButton: {
    color: '#e50914',
    fontSize: 14,
    fontWeight: '600',
  },
  historyList: {
    gap: 8,
  },
  historyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    gap: 12,
  },
  historyText: {
    flex: 1,
    color: '#fff',
    fontSize: 15,
  },
  historyTags: {
    flexDirection: 'row',
    gap: 6,
  },
  historyScopeTag: {
    color: '#888',
    fontSize: 12,
    textTransform: 'capitalize',
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  historyLanguageTag: {
    color: '#e50914',
    fontSize: 12,
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  historyContentTypeTag: {
    color: '#4a9eff',
    fontSize: 12,
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  historyGenreTag: {
    color: '#ffa500',
    fontSize: 12,
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  popularGrid: {
    marginHorizontal: -16,
    paddingHorizontal: 16,
  },
  popularCard: {
    width: 140,
    marginRight: 12,
  },
  popularPoster: {
    width: 140,
    height: 210,
    borderRadius: 8,
    backgroundColor: '#1a1a1a',
  },
  placeholderPoster: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  popularInfo: {
    marginTop: 8,
  },
  popularTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  popularYear: {
    color: '#888',
    fontSize: 12,
  },
  loader: {
    marginVertical: 32,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '70%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
  },
  modalScroll: {
    padding: 16,
  },
  languageOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 8,
    backgroundColor: '#0c0c0c',
  },
  languageOptionActive: {
    backgroundColor: '#2a2a2a',
  },
  languageOptionText: {
    color: '#fff',
    fontSize: 16,
  },
  modeSelector: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 16,
    gap: 8,
  },
  modeButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#1a1a1a',
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
  },
  modeButtonActive: {
    backgroundColor: '#e50914',
  },
  modeButtonText: {
    color: '#888',
    fontSize: 16,
    fontWeight: '600',
  },
  modeButtonTextActive: {
    color: '#fff',
  },
});