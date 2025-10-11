import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

// Conditionally import WebView only for native platforms
let WebView: any;
if (Platform.OS !== 'web') {
  WebView = require('react-native-webview').WebView;
}

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

export default function AIRecommendationsScreen() {
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      Alert.alert('Login Required', 'Please login to use AI recommendations');
      router.replace('/auth');
      return;
    }
    
    initializeChatKit();
  }, [isAuthenticated]);

  const initializeChatKit = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/chatkit/session`);
      setClientSecret(response.data.client_secret);
    } catch (error: any) {
      console.error('Failed to initialize ChatKit:', error);
      const message = error.response?.data?.detail || 'Failed to load AI chat';
      Alert.alert('Error', message);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  if (isLoading || !clientSecret) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#e50914" />
          <Text style={styles.loadingText}>Starting AI assistant...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // HTML content that will be loaded in WebView with ChatKit
  const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <script src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js" async></script>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: #0c0c0c;
      height: 100vh;
      overflow: hidden;
    }
    #chatkit-container {
      width: 100%;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .header {
      background-color: #1a1a1a;
      padding: 16px;
      border-bottom: 1px solid #2a2a2a;
    }
    .header-title {
      color: #fff;
      font-size: 18px;
      font-weight: 600;
    }
    .header-subtitle {
      color: #888;
      font-size: 13px;
      margin-top: 4px;
    }
    #chatkit {
      flex: 1;
      width: 100%;
    }
  </style>
</head>
<body>
  <div id="chatkit-container">
    <div class="header">
      <div class="header-title">🎬 AI Movie Recommendations</div>
      <div class="header-subtitle">Get personalized movie suggestions</div>
    </div>
    <chatkit-root id="chatkit"></chatkit-root>
  </div>
  
  <script>
    (async function() {
      const chatkit = document.getElementById('chatkit');
      const clientSecret = '${clientSecret}';
      
      chatkit.setOptions({
        api: {
          async getClientSecret(currentClientSecret) {
            // Return the client secret we got from the backend
            return clientSecret;
          }
        },
        theme: {
          colors: {
            primary: '#e50914',
            background: '#0c0c0c',
            surface: '#1a1a1a',
            text: '#ffffff',
            textSecondary: '#888888',
          },
          borderRadius: '12px',
        }
      });
    })();
  </script>
</body>
</html>
`;

  // For web platform, use iframe
  if (Platform.OS === 'web') {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <div
          style={{
            flex: 1,
            width: '100%',
            height: '100%',
          }}
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />
      </SafeAreaView>
    );
  }

  // For native platforms (iOS/Android), use WebView
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <WebView
        source={{ html: htmlContent }}
        style={styles.webview}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        startInLoadingState={true}
        renderLoading={() => (
          <View style={styles.webviewLoading}>
            <ActivityIndicator size="large" color="#e50914" />
          </View>
        )}
        onError={(syntheticEvent) => {
          const { nativeEvent } = syntheticEvent;
          console.error('WebView error:', nativeEvent);
          Alert.alert('Error', 'Failed to load chat interface');
        }}
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
    backgroundColor: '#0c0c0c',
  },
  loadingText: {
    color: '#888',
    fontSize: 16,
    marginTop: 16,
  },
  webview: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  webviewLoading: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0c0c0c',
  },
});
