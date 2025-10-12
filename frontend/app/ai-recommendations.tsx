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
      console.log('Fetching ChatKit session from backend...');
      
      const response = await axios.post(`${BACKEND_URL}/api/chatkit/session`);
      console.log('ChatKit session fetched successfully');
      
      setClientSecret(response.data.client_secret);
      setIsLoading(false);
    } catch (error: any) {
      console.error('Failed to initialize ChatKit:', error);
      console.error('Error response:', error.response?.data);
      const message = error.response?.data?.detail || 'Failed to load AI chat';
      Alert.alert('Error', message);
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

  // HTML content that will be loaded with ChatKit
  const htmlContent = `<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script 
    src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
    async
    onload="console.log('ChatKit script loaded successfully')"
    onerror="console.error('Failed to load ChatKit script from CDN')"
  ></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background-color: #0c0c0c;
      height: 100vh;
      overflow: hidden;
    }
    #container {
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
    .header-title { color: #fff; font-size: 18px; font-weight: 600; }
    .header-subtitle { color: #888; font-size: 13px; margin-top: 4px; }
    #chatkit { 
      flex: 1; 
      width: 100%; 
      min-height: 500px;
      display: flex;
      flex-direction: column;
    }
    openai-chatkit {
      --ck-accent-color: #e50914;
      height: 100%;
      width: 100%;
      min-height: 500px;
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
    }
  </style>
</head>
<body>
  <div id="container">
    <div class="header">
      <div class="header-title">🎬 AI Movie Recommendations</div>
      <div class="header-subtitle">Get personalized movie suggestions</div>
    </div>
    <openai-chatkit id="chatkit"></openai-chatkit>
  </div>
  
  <script>
    console.log('ChatKit HTML loaded, starting initialization...');
    
    // Wait for ChatKit custom element to be defined
    async function initializeChatKit() {
      console.log('Waiting for openai-chatkit custom element...');
      
      try {
        // Wait for the custom element to be defined
        await customElements.whenDefined('openai-chatkit');
        console.log('openai-chatkit element is defined!');
        
        const chatkit = document.getElementById('chatkit');
        
        if (!chatkit) {
          console.error('ChatKit element not found in DOM');
          return;
        }
        
        console.log('ChatKit element found, setting options...');
        console.log('setOptions method available:', typeof chatkit.setOptions === 'function');
        
        // Set authentication and theme options
        const clientSecret = '${clientSecret}';
        console.log('Using client secret from parent:', !!clientSecret);
        
        chatkit.setOptions({
          api: {
            getClientSecret: async (existingSecret) => {
              console.log('getClientSecret called, returning pre-fetched secret');
              return clientSecret;
            }
          },
          theme: {
            colorScheme: 'dark',
            color: {
              accent: {
                primary: '#e50914',  // FindFlix red
                level: 2
              }
            },
            radius: 'md',
            density: 'compact'
          },
          widgets: {
            async onAction(action, item) {
              console.log('Widget action triggered:', action);
              
              // Handle movie card clicks
              if (action.type === 'view_movie_details' && action.tmdb_id) {
                console.log('Navigating to movie details:', action.tmdb_id);
                
                // Send message to React Native to navigate
                window.ReactNativeWebView?.postMessage(JSON.stringify({
                  type: 'navigate',
                  screen: 'details',
                  params: {
                    id: action.tmdb_id,
                    mediaType: action.media_type || 'movie'
                  }
                }));
              }
            }
          }
        });
        
        console.log('ChatKit options set successfully!');
        
        // Add event listeners for debugging
        chatkit.addEventListener('chatkit.ready', () => {
          console.log('ChatKit is ready!');
          console.log('ChatKit element computed style:', window.getComputedStyle(chatkit).display);
          console.log('ChatKit element offsetHeight:', chatkit.offsetHeight);
          console.log('ChatKit element offsetWidth:', chatkit.offsetWidth);
          console.log('ChatKit element children:', chatkit.children.length);
          console.log('ChatKit shadowRoot:', chatkit.shadowRoot);
        });
        
        chatkit.addEventListener('chatkit.error', (e) => {
          console.error('ChatKit error:', e.detail);
        });
        
        chatkit.addEventListener('chatkit.response.start', () => {
          console.log('ChatKit response streaming started...');
        });
        
      } catch (error) {
        console.error('Error initializing ChatKit:', error);
      }
    }
    
    // Start initialization when script loads
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initializeChatKit);
    } else {
      initializeChatKit();
    }
  </script>
</body>
</html>`;

  // For web platform, use iframe
  if (Platform.OS === 'web') {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <iframe
          srcDoc={htmlContent}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            flex: 1,
          }}
          title="AI Movie Recommendations"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
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
