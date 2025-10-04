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
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { POPULAR_LANGUAGES } from '../utils/languages';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';
const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500';

type SearchScope = 'title' | 'genre' | 'cast' | 'director';

interface SearchHistoryItem {
  id: string;
  query: string;
  scope: SearchScope;
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
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedScope, setSelectedScope] = useState<SearchScope>('title');
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();

  // Fetch search history
  const { data: searchHistory } = useQuery<SearchHistoryItem[]>({
    queryKey: ['searchHistory'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/search/history?limit=5`);
      return response.data;
    },
  });

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
          language: selectedLanguage 
        },
      });
    }
  };

  const handleHistoryItemClick = (item: SearchHistoryItem) => {
    router.push({
      pathname: '/results',
      params: { query: item.query, scope: item.scope },
    });
  };

  const handlePopularItemClick = (item: PopularTitle) => {
    router.push({
      pathname: '/details',
      params: { id: item.id, mediaType: item.media_type },
    });
  };

  const scopes: SearchScope[] = ['title', 'genre', 'cast', 'director'];
  const selectedLanguageObj = POPULAR_LANGUAGES.find(l => l.code === selectedLanguage);

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
          <Text style={styles.title}>StreamFinder</Text>
          <Text style={styles.subtitle}>Find your next watch</Text>
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
                  <Text style={styles.historyScopeTag}>{item.scope}</Text>
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
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 24,
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
  historyScopeTag: {
    color: '#888',
    fontSize: 12,
    textTransform: 'capitalize',
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
});