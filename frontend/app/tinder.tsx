import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Modal,
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

export default function TinderScreen() {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedFriend, setSelectedFriend] = useState<Friend | null>(null);
  const [sessionData, setSessionData] = useState<any>(null);
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
      const friendsResponse = await axios.get(`${BACKEND_URL}/api/friends`);
      setFriends(friendsResponse.data);
    } catch (error) {
      console.error('Failed to load friends:', error);
      Alert.alert('Error', 'Failed to load friends');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFriendClick = async (friend: Friend) => {
    console.log('Button clicked for friend:', friend.name);
    setIsLoading(true);
    try {
      console.log('Making API call to:', `${BACKEND_URL}/api/swipe/session/${friend.id}`);
      
      // Get or create session with this friend
      const response = await axios.get(`${BACKEND_URL}/api/swipe/session/${friend.id}`);
      const sessionData = response.data;
      
      console.log('Session data received:', sessionData);
      
      // Show custom modal instead of Alert (better for web)
      setSelectedFriend(friend);
      setSessionData(sessionData);
      setShowModal(true);
    } catch (error: any) {
      console.error('Failed to get session:', error);
      console.error('Error response:', error.response?.data);
      Alert.alert('Error', `Failed to load session: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
    }
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

      {/* Content */}
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

      {/* Custom Modal for Options */}
      <Modal
        visible={showModal}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>
              Swipe with {selectedFriend?.name}
            </Text>
            <Text style={styles.modalSubtitle}>
              You have {sessionData?.match_count || 0} matches together
            </Text>

            <TouchableOpacity
              style={styles.modalButton}
              onPress={() => {
                console.log('Continue Swiping selected');
                setShowModal(false);
                router.push({
                  pathname: '/swipe-session',
                  params: { sessionId: sessionData.session_id },
                });
              }}
            >
              <Ionicons name="heart" size={24} color="#fff" />
              <Text style={styles.modalButtonText}>Continue Swiping</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.modalButton, styles.modalButtonSecondary]}
              onPress={() => {
                console.log('View Matches selected');
                setShowModal(false);
                router.push({
                  pathname: '/session-summary',
                  params: { sessionId: sessionData.session_id },
                });
              }}
            >
              <Ionicons name="eye" size={24} color="#e50914" />
              <Text style={[styles.modalButtonText, styles.modalButtonTextSecondary]}>
                View Matches
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.modalCancelButton}
              onPress={() => {
                console.log('Cancelled');
                setShowModal(false);
              }}
            >
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
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