import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

export default function AIRecommendationsScreen() {
  const [state, setState] = React.useState<{
    loading: boolean;
    secret: string | null;
    error: string | null;
  }>({
    loading: true,
    secret: null,
    error: null
  });
  
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  // Single useEffect for initialization
  React.useEffect(() => {
    let mounted = true;

    const init = async () => {
      if (!isAuthenticated) {
        if (mounted) {
          setState({ loading: false, secret: null, error: 'Not authenticated' });
        }
        return;
      }

      try {
        const response = await axios.post(`${BACKEND_URL}/api/chatkit/session`);
        if (mounted) {
          setState({ 
            loading: false, 
            secret: response.data.client_secret, 
            error: null 
          });
        }
      } catch (err: any) {
        if (mounted) {
          setState({ 
            loading: false, 
            secret: null, 
            error: err.response?.data?.detail || 'Failed to load' 
          });
        }
      }
    };

    init();
    return () => { mounted = false; };
  }, [isAuthenticated]);

  // Handle navigation messages
  React.useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      console.log('📥 Parent received message:', event.data);
      
      if (event.data?.type === 'navigate' && event.data?.screen === 'details') {
        console.log('🚀 Navigating to details:', event.data.params);
        
        try {
          router.push({
            pathname: '/details',
            params: event.data.params
          });
          console.log('✅ Navigation successful');
        } catch (error) {
          console.error('❌ Navigation error:', error);
        }
      } else {
        console.log('⚠️ Message ignored (not navigation)');
      }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('message', handleMessage);
      return () => window.removeEventListener('message', handleMessage);
    }
  }, [router]);

  // Not authenticated
  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <Text style={styles.text}>Please login to use AI recommendations</Text>
          <Text style={styles.link} onPress={() => router.push('/auth')}>
            Go to Login
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  // Loading
  if (state.loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#e50914" />
          <Text style={styles.text}>Loading AI assistant...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Error
  if (state.error || !state.secret) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <Text style={styles.text}>{state.error || 'Failed to initialize'}</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Success - render iframe
  const html = `<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js" async></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, sans-serif; background: #0c0c0c; height: 100vh; overflow: hidden; }
    #container { width: 100%; height: 100vh; display: flex; flex-direction: column; }
    .header { background: #1a1a1a; padding: 16px; border-bottom: 1px solid #2a2a2a; }
    .header-title { color: #fff; font-size: 18px; font-weight: 600; }
    .header-subtitle { color: #888; font-size: 13px; margin-top: 4px; }
    #chatkit { flex: 1; width: 100%; min-height: 500px; display: block; }
    openai-chatkit { --ck-accent: #e50914; height: 100%; width: 100%; display: block; }
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
    (async function() {
      console.log('⚙️ ChatKit script starting...');
      
      try {
        console.log('⏳ Waiting for openai-chatkit element...');
        await customElements.whenDefined('openai-chatkit');
        console.log('✅ openai-chatkit element defined');
        
        const chatkit = document.getElementById('chatkit');
        console.log('📍 ChatKit element:', chatkit);
        console.log('📍 setOptions available:', typeof chatkit.setOptions);
        
        chatkit.setOptions({
          api: {
            getClientSecret: async () => {
              console.log('🔑 getClientSecret called');
              return '${state.secret}';
            }
          },
          theme: 'dark',
          widgets: {
            async onAction(action) {
              console.log('🔵 Widget action triggered:', action);
              console.log('🔵 Action type:', action.type);
              console.log('🔵 Action payload:', action.payload);
            
            if (action.type === 'view_movie_details' && action.payload?.movie_name) {
              const movieName = action.payload.movie_name;
              console.log('🔍 Searching for movie:', movieName);
              
              try {
                const res = await fetch('${BACKEND_URL}/api/search', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ query: movieName, scope: 'title', page: 1 })
                });
                
                console.log('🔍 Search response status:', res.status);
                const data = await res.json();
                console.log('🔍 Search results:', data);
                
                if (data.results?.[0]) {
                  const movie = data.results[0];
                  console.log('✅ Found movie:', movie);
                  
                  const message = {
                    type: 'navigate',
                    screen: 'details',
                    params: { id: movie.id, mediaType: movie.media_type }
                  };
                  console.log('📤 Sending message to parent:', message);
                  
                  window.parent.postMessage(message, '*');
                  console.log('✅ Message sent successfully');
                } else {
                  console.warn('⚠️ No results found for:', movieName);
                }
              } catch (e) {
                console.error('❌ Error in onAction:', e);
              }
            } else {
              console.warn('⚠️ Action not handled:', action);
            }
          }
        }
      });
    })();
  </script>
</body>
</html>`;

  return (
    <SafeAreaView style={styles.container}>
      <iframe
        srcDoc={html}
        style={{ width: '100%', height: '100%', border: 'none', flex: 1 }}
        title="AI Movie Recommendations"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0c0c0c' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  text: { color: '#fff', fontSize: 18, textAlign: 'center', marginBottom: 20 },
  link: { color: '#e50914', fontSize: 16, fontWeight: '600', textDecorationLine: 'underline' },
});
