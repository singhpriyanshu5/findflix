import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

interface ProfileStats {
  friends_count: number;
  pending_requests_count: number;
  total_sessions: number;
  total_matches: number;
}

export default function ProfileScreen() {
  const [stats, setStats] = useState<ProfileStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { user, isAuthenticated, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/auth');
      return;
    }
    
    loadStats();
  }, [isAuthenticated]);

  const loadStats = async () => {
    setIsLoading(true);
    try {
      // Fetch all data in parallel
      const [friendsRes, receivedReqRes, sentReqRes, sessionsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/friends`),
        axios.get(`${BACKEND_URL}/api/friends/requests`),
        axios.get(`${BACKEND_URL}/api/friends/requests/sent`),
        axios.get(`${BACKEND_URL}/api/swipe/sessions`),
      ]);

      const friends = friendsRes.data;
      const receivedRequests = receivedReqRes.data;
      const sentRequests = sentReqRes.data;
      const sessions = sessionsRes.data;

      // Calculate total matches across all sessions
      let totalMatches = 0;
      for (const session of sessions) {
        try {
          const matchesRes = await axios.get(`${BACKEND_URL}/api/swipe/matches/${session.id}`);
          totalMatches += matchesRes.data.length;
        } catch (error) {
          console.error('Failed to load matches for session:', session.id);
        }
      }

      setStats({
        friends_count: friends.length,
        pending_requests_count: receivedRequests.length + sentRequests.length,
        total_sessions: sessions.length,
        total_matches: totalMatches,
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
      // Set default stats if there's an error
      setStats({
        friends_count: 0,
        pending_requests_count: 0,
        total_sessions: 0,
        total_matches: 0,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: () => {
            logout();
            router.replace('/auth');
          },
        },
      ]
    );
  };

  if (!isAuthenticated) {
    return null;
  }

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#fff" />
          <Text style={styles.loadingText}>Loading profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user?.name.charAt(0).toUpperCase()}
            </Text>
          </View>
          <Text style={styles.name}>{user?.name}</Text>
          <Text style={styles.email}>{user?.email}</Text>
        </View>

        {/* Stats Cards */}
        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <View style={styles.statIconContainer}>
              <Ionicons name="people" size={24} color="#e50914" />
            </View>
            <Text style={styles.statNumber}>{stats?.friends_count || 0}</Text>
            <Text style={styles.statLabel}>Friends</Text>
          </View>

          <View style={styles.statCard}>
            <View style={styles.statIconContainer}>
              <Ionicons name="mail" size={24} color="#e50914" />
            </View>
            <Text style={styles.statNumber}>{stats?.pending_requests_count || 0}</Text>
            <Text style={styles.statLabel}>Pending Invites</Text>
          </View>

          <View style={styles.statCard}>
            <View style={styles.statIconContainer}>
              <Ionicons name="heart" size={24} color="#e50914" />
            </View>
            <Text style={styles.statNumber}>{stats?.total_matches || 0}</Text>
            <Text style={styles.statLabel}>Total Matches</Text>
          </View>

          <View style={styles.statCard}>
            <View style={styles.statIconContainer}>
              <Ionicons name="film" size={24} color="#e50914" />
            </View>
            <Text style={styles.statNumber}>{stats?.total_sessions || 0}</Text>
            <Text style={styles.statLabel}>Swipe Sessions</Text>
          </View>
        </View>

        {/* Account Actions */}
        <View style={styles.actionsContainer}>
          <Text style={styles.sectionTitle}>Account</Text>
          
          <TouchableOpacity
            style={styles.actionItem}
            onPress={() => router.push('/tinder')}
          >
            <View style={styles.actionLeft}>
              <Ionicons name="heart-outline" size={24} color="#fff" />
              <Text style={styles.actionText}>Movie Tinder</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#666" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionItem}
            onPress={() => router.push('/add-friend')}
          >
            <View style={styles.actionLeft}>
              <Ionicons name="person-add-outline" size={24} color="#fff" />
              <Text style={styles.actionText}>Add Friends</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#666" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionItem}
            onPress={() => router.push('/recent-searches')}
          >
            <View style={styles.actionLeft}>
              <Ionicons name="time-outline" size={24} color="#fff" />
              <Text style={styles.actionText}>Recent Searches</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#666" />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionItem, styles.logoutAction]}
            onPress={handleLogout}
          >
            <View style={styles.actionLeft}>
              <Ionicons name="log-out-outline" size={24} color="#ef4444" />
              <Text style={[styles.actionText, styles.logoutText]}>Sign Out</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#ef4444" />
          </TouchableOpacity>
        </View>

        {/* App Info */}
        <View style={styles.appInfo}>
          <Text style={styles.appInfoText}>FindFlix</Text>
          <Text style={styles.appVersion}>Version 1.0.0</Text>
        </View>
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
    paddingBottom: 32,
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
    alignItems: 'center',
    paddingVertical: 32,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#e50914',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  avatarText: {
    color: '#fff',
    fontSize: 36,
    fontWeight: 'bold',
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  email: {
    fontSize: 16,
    color: '#888',
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 32,
  },
  statCard: {
    width: '48%',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    marginBottom: 16,
  },
  statIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(229, 9, 20, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  statNumber: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
  },
  actionsContainer: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 16,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  actionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  actionText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '500',
  },
  logoutAction: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderWidth: 1,
    borderColor: '#ef4444',
  },
  logoutText: {
    color: '#ef4444',
  },
  appInfo: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  appInfoText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#e50914',
    marginBottom: 4,
  },
  appVersion: {
    fontSize: 12,
    color: '#666',
  },
});
