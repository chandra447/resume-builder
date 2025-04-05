import { useState, useEffect } from 'react';
import {
  AppBar,
  Box,
  Button,
  CircularProgress,
  Container,
  CssBaseline,
  Paper,
  ThemeProvider,
  Toolbar,
  Typography,
  Alert,
} from '@mui/material';
import { UploadDialog } from './components/UploadDialog';
import { ChatPanel } from './components/ChatPanel';
import { MarkdownPreview } from './components/MarkdownPreview';
import { api } from './services/api';
import { theme } from './theme/theme';
import './App.css';

function App() {
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<any>(null);
  const [loading, setLoading] = useState(false); // Initialize loading as false
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Array<{role: string; content: string}>>([
    { role: 'system', content: 'Welcome to the Resume Builder! Upload your resume and a job description to get started.' }
  ]);

  // Ensure loading state is false when component mounts
  useEffect(() => {
    console.log('Component mounted, ensuring loading state is false');
    setLoading(false);
  }, []);

  // WebSocket connection is disabled for now
  // We'll use polling instead to check for updates
  
  // Poll for updates every 5 seconds when there's an active session
  useEffect(() => {
    if (!sessionId) return;
    
    console.log('Setting up polling for session updates');
    const intervalId = setInterval(() => {
      fetchSessionState();
    }, 5000);
    
    return () => {
      console.log('Clearing polling interval');
      clearInterval(intervalId);
    };
  }, [sessionId]);

  // Fetch session state when sessionId changes
  useEffect(() => {
    if (sessionId) {
      fetchSessionState();
    }
  }, [sessionId]);

  const fetchSessionState = async () => {
    if (!sessionId) return;
    
    console.log('Fetching session state...');
    setLoading(true);
    try {
      const response = await api.get(`/api/v1/tailoring-sessions/${sessionId}`);
      console.log('Session state fetched successfully:', response.data);
      setSessionState(response.data.state);
    } catch (err: any) {
      console.error('Error fetching session state:', err);
      setError(err.response?.data?.detail || 'Failed to fetch session data');
    } finally {
      // Always set loading to false when the operation completes, regardless of success or failure
      setLoading(false);
      console.log('Loading state set to false');
    }
  };

  const handleUploadSuccess = (id: string) => {
    setSessionId(id);
    setMessages(prev => [
      ...prev,
      { role: 'system', content: 'Resume and job description uploaded successfully! Processing...' }
    ]);
  };

  const handleSendFeedback = async (feedback: any) => {
    if (!sessionId) return;
    
    console.log('Sending feedback...');
    setLoading(true);
    try {
      // Add user message to chat
      setMessages(prev => [...prev, { role: 'user', content: feedback.message || 'Provided feedback' }]);
      
      // Send feedback to backend
      const response = await api.post(`/api/v1/tailoring-sessions/${sessionId}/feedback`, {
        feedback
      });
      
      console.log('Feedback sent successfully:', response.data);
      // Update session state
      setSessionState(response.data.state);
    } catch (err: any) {
      console.error('Error sending feedback:', err);
      setError(err.response?.data?.detail || 'Failed to send feedback');
    } finally {
      // Always set loading to false when the operation completes, regardless of success or failure
      setLoading(false);
      console.log('Loading state set to false after feedback');
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Resume Builder
            </Typography>
            <Button color="inherit" onClick={() => setUploadDialogOpen(true)}>
              Upload Resume
            </Button>
          </Toolbar>
        </AppBar>

        <Container maxWidth="lg" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {loading && sessionId && (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          )}

          <Box display="flex" gap={2} height="calc(100vh - 200px)">
            {/* Chat Panel */}
            <Paper sx={{ width: '40%', p: 2, overflow: 'auto' }}>
              <ChatPanel 
                messages={messages} 
                onSendMessage={(message) => handleSendFeedback({ message })} 
                disabled={loading || !sessionId}
              />
            </Paper>

            {/* Resume Preview */}
            <Paper sx={{ width: '60%', p: 2, overflow: 'auto' }}>
              {sessionState?.tailored_resume ? (
                <MarkdownPreview content={sessionState.tailored_resume} />
              ) : (
                <Typography variant="body1" color="text.secondary" textAlign="center" mt={10}>
                  Upload your resume and a job description to see the tailored result here.
                </Typography>
              )}
            </Paper>
          </Box>
        </Container>

        <UploadDialog 
          open={uploadDialogOpen} 
          onClose={() => setUploadDialogOpen(false)} 
          onSuccess={handleUploadSuccess}
        />
      </Box>
    </ThemeProvider>
  );
}

export default App;
