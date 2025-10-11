import { Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { StatusBar } from 'expo-status-bar';
import { AuthProvider } from '../contexts/AuthContext';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 60 * 72, // 72 hours
      gcTime: 1000 * 60 * 60 * 72,
      retry: 2,
    },
  },
});

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <StatusBar style="light" />
          <Stack
            screenOptions={{
              headerStyle: {
                backgroundColor: '#1a1a1a',
              },
              headerTintColor: '#fff',
              headerTitleStyle: {
                fontWeight: '600',
              },
              contentStyle: {
                backgroundColor: '#0c0c0c',
              },
            }}
          >
            <Stack.Screen 
              name="index" 
              options={{
                headerShown: false,
              }}
            />
            <Stack.Screen 
              name="auth" 
              options={{
                headerShown: false,
              }}
            />
            <Stack.Screen 
              name="tinder" 
              options={{
                title: 'Movie Tinder',
              }}
            />
            <Stack.Screen 
              name="add-friend" 
              options={{
                title: 'Add Friend',
              }}
            />
            <Stack.Screen 
              name="create-session" 
              options={{
                title: 'Create Session',
              }}
            />
            <Stack.Screen 
              name="swipe-session" 
              options={{
                title: 'Swipe Movies',
              }}
            />
            <Stack.Screen 
              name="session-summary" 
              options={{
                title: 'Your Matches',
              }}
            />
            <Stack.Screen 
              name="results" 
              options={{
                title: 'Results',
              }}
            />
            <Stack.Screen 
              name="details" 
              options={{
                title: 'Details',
              }}
            />
            <Stack.Screen 
              name="profile" 
              options={{
                title: 'Profile',
              }}
            />
            <Stack.Screen 
              name="recent-searches" 
              options={{
                title: 'Recent Searches',
              }}
            />
            <Stack.Screen 
              name="ai-recommendations" 
              options={{
                title: 'AI Movie Recommendations',
              }}
            />
          </Stack>
        </AuthProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}