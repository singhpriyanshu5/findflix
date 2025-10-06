import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { FlashList } from '@shopify/flash-list';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

interface FriendRequest {
  id: string;
  sender: {
    id: string;
    name: string;
    email: string;
  };
  receiver: {
    id: string;
    name: string;
    email: string;
  };
  status: 'pending' | 'accepted' | 'declined';
  created_at: string;
}

export default function AddFriendScreen() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [friendRequests, setFriendRequests] = useState<FriendRequest[]>([]);
  const [isLoadingRequests, setIsLoadingRequests] = useState(true);
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/auth');
      return;
    }
    
    loadFriendRequests();
  }, [isAuthenticated]);

  const loadFriendRequests = async () => {
    setIsLoadingRequests(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/friends/requests`);
      setFriendRequests(response.data);
    } catch (error) {
      console.error('Failed to load friend requests:', error);
    } finally {
      setIsLoadingRequests(false);
    }
  };

  const sendFriendRequest = async () => {
    if (!email.trim()) {
      Alert.alert('Error', 'Please enter an email address');
      return;
    }

    setIsLoading(true);
    try {
      await axios.post(`${BACKEND_URL}/api/friends/request`, {
        receiver_email: email.trim(),
      });
      
      Alert.alert('Success', 'Friend request sent successfully!');
      setEmail('');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to send friend request';
      Alert.alert('Error', message);
    } finally {
      setIsLoading(false);
    }
  };

  const respondToRequest = async (requestId: string, accept: boolean) => {
    try {
      await axios.post(`${BACKEND_URL}/api/friends/respond`, {
        request_id: requestId,
        accept,
      });
      
      Alert.alert(
        'Success', 
        accept ? 'Friend request accepted!' : 'Friend request declined!'
      );
      
      // Reload requests
      loadFriendRequests();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to respond to friend request';
      Alert.alert('Error', message);
    }
  };

  const renderFriendRequest = ({ item }: { item: FriendRequest }) => (
    <View style={styles.requestCard}>
      <View style={styles.requestInfo}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {item.sender.name.charAt(0).toUpperCase()}
          </Text>
        </View>
        <View style={styles.requestDetails}>
          <Text style={styles.requestName}>{item.sender.name}</Text>
          <Text style={styles.requestEmail}>{item.sender.email}</Text>
          <Text style={styles.requestDate}>
            {new Date(item.created_at).toLocaleDateString()}
          </Text>
        </View>
      </View>
      
      <View style={styles.requestActions}>
        <TouchableOpacity
          style={[styles.actionButton, styles.acceptButton]}
          onPress={() => respondToRequest(item.id, true)}
        >
          <Ionicons name="checkmark" size={20} color="#fff" />
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.declineButton]}
          onPress={() => respondToRequest(item.id, false)}
        >
          <Ionicons name="close" size={20} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );

  if (!isAuthenticated) {
    return null;
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        {/* Send Friend Request */}
        <View style={styles.sendSection}>
          <Text style={styles.sectionTitle}>Send Friend Request</Text>
          <View style={styles.inputContainer}>
            <Ionicons name="mail-outline" size={20} color="#888" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Enter friend's email address"
              placeholderTextColor="#666"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />
          </View>
          <TouchableOpacity
            style={styles.sendButton}
            onPress={sendFriendRequest}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="person-add" size={20} color="#fff" />
                <Text style={styles.sendButtonText}>Send Request</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Pending Friend Requests */}
        <View style={styles.requestsSection}>
          <Text style={styles.sectionTitle}>Pending Friend Requests</Text>
          
          {isLoadingRequests ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#fff" />
              <Text style={styles.loadingText}>Loading requests...</Text>
            </View>
          ) : friendRequests.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="people-outline" size={48} color="#666" />
              <Text style={styles.emptyText}>No pending friend requests</Text>
            </View>
          ) : (
            <FlashList
              data={friendRequests}
              renderItem={renderFriendRequest}
              keyExtractor={(item) => item.id}
              estimatedItemSize={80}
              contentContainerStyle={styles.listContent}
            />
          )}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  keyboardView: {
    flex: 1,
  },
  sendSection: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a1a',
  },
  requestsSection: {
    flex: 1,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 4,
    marginBottom: 16,
  },
  inputIcon: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    color: '#fff',
    fontSize: 16,
    paddingVertical: 12,
  },
  sendButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e50914',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  sendButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 32,
    gap: 12,
  },
  loadingText: {
    color: '#888',
    fontSize: 14,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 64,
  },
  emptyText: {
    color: '#888',
    fontSize: 16,
    marginTop: 12,
  },
  listContent: {
    paddingBottom: 16,
  },
  requestCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  requestInfo: {
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
  requestDetails: {
    flex: 1,
  },
  requestName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 2,
  },
  requestEmail: {
    fontSize: 14,
    color: '#888',
    marginBottom: 2,
  },
  requestDate: {
    fontSize: 12,
    color: '#666',
  },
  requestActions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  acceptButton: {
    backgroundColor: '#22c55e',
  },
  declineButton: {
    backgroundColor: '#ef4444',
  },
});