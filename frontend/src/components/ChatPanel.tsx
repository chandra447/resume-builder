import React, { useState, useRef, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    TextField,
    Button,
    CircularProgress,
    IconButton,
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const ChatContainer = styled(Paper)(({ theme }) => ({
    height: '500px',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    backgroundColor: theme.palette.background.paper,
}));

const MessagesContainer = styled(Box)(({ theme }) => ({
    flex: 1,
    overflow: 'auto',
    padding: theme.spacing(2),
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing(2),
}));

const Message = styled(Box, {
    shouldForwardProp: (prop) => prop !== 'isUser',
})<{ isUser?: boolean }>(({ theme, isUser }) => ({
    maxWidth: '80%',
    alignSelf: isUser ? 'flex-end' : 'flex-start',
    backgroundColor: isUser ? theme.palette.primary.main : theme.palette.grey[100],
    color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
    padding: theme.spacing(1.5),
    borderRadius: theme.spacing(2),
    position: 'relative',
}));

const InputContainer = styled(Box)(({ theme }) => ({
    padding: theme.spacing(2),
    borderTop: `1px solid ${theme.palette.divider}`,
    display: 'flex',
    gap: theme.spacing(1),
}));

interface ChatMessage {
    id: string;
    text: string;
    isUser: boolean;
    timestamp: Date;
}

interface ChatPanelProps {
    sessionId: string;
    onSendMessage: (message: string) => Promise<void>;
    loading?: boolean;
    messages: ChatMessage[];
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
    sessionId,
    onSendMessage,
    loading = false,
    messages,
}) => {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        try {
            await onSendMessage(input);
            setInput('');
        } catch (error) {
            console.error('Failed to send message:', error);
        }
    };

    const handleKeyPress = (event: React.KeyboardEvent) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSend();
        }
    };

    return (
        <ChatContainer elevation={0}>
            <MessagesContainer>
                {messages.map((message) => (
                    <Message key={message.id} isUser={message.isUser}>
                        <Typography variant="body1">{message.text}</Typography>
                        <Typography
                            variant="caption"
                            sx={{
                                position: 'absolute',
                                bottom: -20,
                                right: message.isUser ? 8 : 'auto',
                                left: message.isUser ? 'auto' : 8,
                                color: 'text.secondary',
                            }}
                        >
                            {message.timestamp.toLocaleTimeString()}
                        </Typography>
                    </Message>
                ))}
                {loading && (
                    <Box display="flex" justifyContent="center" my={2}>
                        <CircularProgress size={24} />
                    </Box>
                )}
                <div ref={messagesEndRef} />
            </MessagesContainer>
            <InputContainer>
                <TextField
                    fullWidth
                    multiline
                    maxRows={4}
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={loading}
                    variant="outlined"
                    size="small"
                />
                <IconButton
                    color="primary"
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                >
                    <SendIcon />
                </IconButton>
            </InputContainer>
        </ChatContainer>
    );
}; 