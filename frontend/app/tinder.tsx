import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { FlashList } from '@shopify/flash-list';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

interface Friend {
  id: string;
  name: string;
  email: string;
  picture?: string;
}

interface SwipeSession {
  id: string;
  creator: Friend;
  friend: Friend;
  content_type: 'popular' | 'search' | 'genre';
  content_params: Record<string, any>;
  is_active: boolean;
  created_at: string;
  my_swipes_count: number;
  friend_swipes_count: number;
}

export default function TinderScreen() {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/auth');
      return;
    }
    
    loadData();
  }, [isAuthenticated]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [friendsResponse, sessionsResponse] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/friends`),
        axios.get(`${BACKEND_URL}/api/swipe/sessions`),
      ]);
      
      setFriends(friendsResponse.data);
      setSessions(sessionsResponse.data);
    } catch (error) {
      console.error('Failed to load data:', error);
      Alert.alert('Error', 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFriendClick = async (friend: Friend) => {
    setIsLoading(true);
    try {
      // Get or create session with this friend
      const response = await axios.get(`${BACKEND_URL}/api/swipe/session/${friend.id}`);
      const sessionData = response.data;
      
      // Show options modal
      Alert.alert(
        `Swipe with ${friend.name}`,
        `You have ${sessionData.match_count} matches together`,
        [
          {
            text: 'View Matches',
            onPress: () => router.push({
              pathname: '/session-summary',
              params: { sessionId: sessionData.session_id },
            }),
          },
          {
            text: 'Continue Swiping',
            style: 'default',
            onPress: () => router.push({
              pathname: '/swipe-session',
              params: { sessionId: sessionData.session_id },
            }),
          },
          {
            text: 'Cancel',
            style: 'cancel',
          },
        ]
      );
    } catch (error) {
      console.error('Failed to get session:', error);
      Alert.alert('Error', 'Failed to load session with friend');
    } finally {
      setIsLoading(false);
    }
  };

  const joinSession = (session: SwipeSession) => {
    router.push({
      pathname: '/swipe-session',
      params: { sessionId: session.id },
    });
  };

  const addFriend = () => {
    router.push('/add-friend');
  };

  const renderFriend = ({ item }: { item: Friend }) => (
    <View style={styles.friendCard}>
      <View style={styles.friendInfo}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{item.name.charAt(0).toUpperCase()}</Text>
        </View>
        <View style={styles.friendDetails}>
          <Text style={styles.friendName}>{item.name}</Text>
          <Text style={styles.friendEmail}>{item.email}</Text>
        </View>
      </View>
      <TouchableOpacity
        style={styles.swipeButton}
        onPress={() => handleFriendClick(item)}
        disabled={isLoading}
      >
        <Ionicons name="heart" size={20} color="#fff" />
        <Text style={styles.swipeButtonText}>Swipe Movies</Text>
      </TouchableOpacity>
    </View>
  );

  const renderSession = ({ item }: { item: SwipeSession }) => (
    <View style={styles.sessionCard}>
      <View style={styles.sessionHeader}>
        <Text style={styles.sessionTitle}>
          Swipe Session with {item.creator.id === user?.id ? item.friend.name : item.creator.name}
        </Text>
        <View style={[
          styles.statusBadge,
          item.is_active ? styles.statusActive : styles.statusInactive
        ]}>
          <Text style={styles.statusText}>{item.is_active ? 'Active' : 'Ended'}</Text>
        </View>
      </View>
      
      <View style={styles.sessionStats}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{item.my_swipes_count}</Text>
          <Text style={styles.statLabel}>Your Swipes</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{item.friend_swipes_count}</Text>
          <Text style={styles.statLabel}>Friend's Swipes</Text>
        </View>
      </View>

      <View style={styles.sessionMeta}>
        <Text style={styles.contentType}>
          Content: {item.content_type.charAt(0).toUpperCase() + item.content_type.slice(1)}
        </Text>
      </View>

      {item.is_active && (
        <TouchableOpacity
          style={styles.joinButton}
          onPress={() => joinSession(item)}
        >
          <Text style={styles.joinButtonText}>Continue Swiping</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  if (!isAuthenticated) {
    return null;
  }

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#fff" />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Movie Tinder</Text>
        <Text style={styles.subtitle}>Swipe movies with your friends</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'sessions' && styles.activeTab]}
          onPress={() => setActiveTab('sessions')}
        >
          <Text style={[styles.tabText, activeTab === 'sessions' && styles.activeTabText]}>
            Sessions ({sessions.length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'friends' && styles.activeTab]}
          onPress={() => setActiveTab('friends')}
        >
          <Text style={[styles.tabText, activeTab === 'friends' && styles.activeTabText]}>
            Friends ({friends.length})
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      {activeTab === 'friends' ? (
        <View style={styles.content}>
          {friends.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="people-outline" size={64} color="#666" />
              <Text style={styles.emptyTitle}>No Friends Yet</Text>
              <Text style={styles.emptyText}>
                Add friends to start swiping movies together!
              </Text>
              <TouchableOpacity style={styles.addButton} onPress={addFriend}>
                <Text style={styles.addButtonText}>Add Friends</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              <FlashList
                data={friends}
                renderItem={renderFriend}
                keyExtractor={(item) => item.id}
                estimatedItemSize={80}
                contentContainerStyle={styles.listContent}
              />
              <TouchableOpacity style={styles.fab} onPress={addFriend}>
                <Ionicons name="add" size={24} color="#fff" />
              </TouchableOpacity>
            </>
          )}
        </View>
      ) : (
        <View style={styles.content}>
          {sessions.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="heart-outline" size={64} color="#666" />
              <Text style={styles.emptyTitle}>No Sessions Yet</Text>
              <Text style={styles.emptyText}>
                Start a swipe session with a friend to find movies to watch together!
              </Text>
              {friends.length > 0 ? (
                <TouchableOpacity
                  style={styles.addButton}
                  onPress={() => setActiveTab('friends')}
                >
                  <Text style={styles.addButtonText}>Start Swiping</Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity style={styles.addButton} onPress={addFriend}>
                  <Text style={styles.addButtonText}>Add Friends First</Text>
                </TouchableOpacity>
              )}
            </View>
          ) : (
            <FlashList
              data={sessions}
              renderItem={renderSession}
              keyExtractor={(item) => item.id}
              estimatedItemSize={120}
              contentContainerStyle={styles.listContent}
            />
          )}
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
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    marginHorizontal: 4,
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: '#e50914',
  },
  tabText: {
    color: '#888',
    fontSize: 14,
    fontWeight: '600',
  },
  activeTabText: {
    color: '#fff',
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
  },
  listContent: {
    paddingBottom: 80,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
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
  },
  addButton: {
    backgroundColor: '#e50914',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  friendCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  friendInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#e50914',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  avatarText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  friendDetails: {
    flex: 1,
  },
  friendName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  friendEmail: {
    fontSize: 14,
    color: '#888',
  },
  swipeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e50914',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    gap: 6,
  },
  swipeButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  sessionCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  sessionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  sessionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    flex: 1,
    marginRight: 8,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusActive: {
    backgroundColor: '#22c55e',
  },
  statusInactive: {
    backgroundColor: '#888',
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  sessionStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
    paddingVertical: 12,
    backgroundColor: '#0c0c0c',
    borderRadius: 8,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#e50914',
  },
  statLabel: {
    fontSize: 12,
    color: '#888',
    marginTop: 4,
  },
  sessionMeta: {
    marginBottom: 12,
  },
  contentType: {
    fontSize: 14,
    color: '#aaa',
  },
  joinButton: {
    backgroundColor: '#e50914',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  joinButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#e50914',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
});