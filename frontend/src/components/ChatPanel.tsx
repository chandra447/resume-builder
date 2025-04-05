import React, { useState, useRef, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    TextField,
    CircularProgress,
    IconButton,
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const ChatContainer = styled(Paper)(({ theme }) => ({
    height: '100%',
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
    maxWidth: '90%',
    alignSelf: isUser ? 'flex-end' : 'flex-start',
    backgroundColor: isUser ? theme.palette.primary.main : theme.palette.grey[100],
    color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
    padding: theme.spacing(1.5),
    borderRadius: theme.spacing(2),
    position: 'relative',
    marginBottom: theme.spacing(1),
    wordBreak: 'break-word',
}));

const InputContainer = styled(Box)(({ theme }) => ({
    padding: theme.spacing(2),
    borderTop: `1px solid ${theme.palette.divider}`,
    display: 'flex',
    gap: theme.spacing(1),
}));

interface ChatPanelProps {
    messages: Array<{role: string; content: string}>;
    onSendMessage: (message: string) => void;
    disabled?: boolean;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
    messages,
    onSendMessage,
    disabled = false,
}) => {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = () => {
        if (!input.trim() || disabled) return;

        onSendMessage(input);
        setInput('');
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
                {messages.map((message, index) => {
                    const isUser = message.role === 'user';
                    const isSystem = message.role === 'system';
                    
                    return (
                        <Message 
                            key={index} 
                            isUser={isUser}
                            sx={{
                                backgroundColor: isSystem 
                                    ? 'rgba(0, 0, 0, 0.05)' 
                                    : isUser 
                                        ? (theme) => theme.palette.primary.main 
                                        : (theme) => theme.palette.grey[100],
                                color: isSystem
                                    ? (theme) => theme.palette.text.secondary
                                    : isUser
                                        ? (theme) => theme.palette.primary.contrastText
                                        : (theme) => theme.palette.text.primary,
                                fontStyle: isSystem ? 'italic' : 'normal',
                            }}
                        >
                            <Typography variant="body1">{message.content}</Typography>
                        </Message>
                    );
                })}
                {disabled && (
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
                    disabled={disabled}
                    variant="outlined"
                    size="small"
                />
                <IconButton
                    color="primary"
                    onClick={handleSend}
                    disabled={disabled || !input.trim()}
                >
                    <SendIcon />
                </IconButton>
            </InputContainer>
        </ChatContainer>
    );
}; 