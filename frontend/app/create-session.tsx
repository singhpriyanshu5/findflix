import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

type ContentType = 'popular' | 'search' | 'genre';

interface ContentOption {
  type: ContentType;
  title: string;
  description: string;
  icon: string;
}

const contentOptions: ContentOption[] = [
  {
    type: 'popular',
    title: 'Popular Movies & Shows',
    description: 'Swipe through trending and popular titles',
    icon: 'trending-up',
  },
  {
    type: 'genre',
    title: 'By Genre',
    description: 'Focus on specific genres you both like',
    icon: 'film',
  },
  {
    type: 'search',
    title: 'Search Results',
    description: 'Swipe through search results for specific titles',
    icon: 'search',
  },
];

export default function CreateSessionScreen() {
  const [selectedType, setSelectedType] = useState<ContentType>('popular');
  const [isLoading, setIsLoading] = useState(false);
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const params = useLocalSearchParams();

  const friendId = params.friendId as string;
  const friendName = params.friendName as string;

  if (!isAuthenticated) {
    router.replace('/auth');
    return null;
  }

  const createSession = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/swipe/session`, {
        friend_id: friendId,
        content_type: selectedType,
        content_params: {},
      });

      const sessionId = response.data.session_id;
      
      Alert.alert(
        'Session Created!',
        `Start swiping with ${friendName}`,
        [
          {
            text: 'Start Swiping',
            onPress: () => {
              router.replace({
                pathname: '/swipe-session',
                params: { sessionId },
              });
            },
          },
        ]
      );
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to create session';
      Alert.alert('Error', message);
    } finally {
      setIsLoading(false);
    }
  };

  const renderContentOption = (option: ContentOption) => (
    <TouchableOpacity
      key={option.type}
      style={[
        styles.optionCard,
        selectedType === option.type && styles.optionCardSelected,
      ]}
      onPress={() => setSelectedType(option.type)}
    >
      <View style={styles.optionContent}>
        <View style={[
          styles.optionIcon,
          selectedType === option.type && styles.optionIconSelected,
        ]}>
          <Ionicons 
            name={option.icon as any} 
            size={24} 
            color={selectedType === option.type ? '#fff' : '#888'} 
          />
        </View>
        <View style={styles.optionText}>
          <Text style={[
            styles.optionTitle,
            selectedType === option.type && styles.optionTitleSelected,
          ]}>
            {option.title}
          </Text>
          <Text style={styles.optionDescription}>
            {option.description}
          </Text>
        </View>
      </View>
      {selectedType === option.type && (
        <View style={styles.checkmark}>
          <Ionicons name="checkmark-circle" size={24} color="#e50914" />
        </View>
      )}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Create Swipe Session</Text>
          <Text style={styles.subtitle}>
            Choose what type of content to swipe with {friendName}
          </Text>
        </View>

        {/* Content Options */}
        <View style={styles.optionsSection}>
          <Text style={styles.sectionTitle}>Content Type</Text>
          {contentOptions.map(renderContentOption)}
        </View>

        {/* Additional Info */}
        {selectedType === 'popular' && (
          <View style={styles.infoBox}>
            <Ionicons name="information-circle-outline" size={20} color="#4a9eff" />
            <Text style={styles.infoText}>
              You'll swipe through the most popular movies and TV shows currently trending.
            </Text>
          </View>
        )}

        {selectedType === 'genre' && (
          <View style={styles.infoBox}>
            <Ionicons name="information-circle-outline" size={20} color="#4a9eff" />
            <Text style={styles.infoText}>
              Choose a specific genre to focus your swiping session. Perfect for finding something specific to watch.
            </Text>
          </View>
        )}

        {selectedType === 'search' && (
          <View style={styles.infoBox}>
            <Ionicons name="information-circle-outline" size={20} color="#4a9eff" />
            <Text style={styles.infoText}>
              Swipe through results from a specific search query. Great for finding similar movies or shows.
            </Text>
          </View>
        )}

        {/* Create Button */}
        <TouchableOpacity
          style={styles.createButton}
          onPress={createSession}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Ionicons name="heart" size={20} color="#fff" />
              <Text style={styles.createButtonText}>Start Swiping Session</Text>
            </>
          )}
        </TouchableOpacity>
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
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#888',
    lineHeight: 22,
  },
  optionsSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 16,
  },
  optionCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  optionCardSelected: {
    borderColor: '#e50914',
    backgroundColor: '#2a1a1a',
  },
  optionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#2a2a2a',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  optionIconSelected: {
    backgroundColor: '#e50914',
  },
  optionText: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  optionTitleSelected: {
    color: '#fff',
  },
  optionDescription: {
    fontSize: 14,
    color: '#888',
    lineHeight: 20,
  },
  checkmark: {
    position: 'absolute',
    top: 12,
    right: 12,
  },
  infoBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#1a2332',
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
    gap: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#aaa',
    lineHeight: 20,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e50914',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
    marginTop: 'auto',
  },
  createButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});