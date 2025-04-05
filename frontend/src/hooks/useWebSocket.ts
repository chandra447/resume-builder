import { useState, useCallback, useEffect } from 'react';

export interface WebSocketMessage {
    type: string;
    question?: string;
    message?: string;
    content?: string;
    data?: string;
    state?: any;
}

export function useWebSocket(url: string | null) {
    const [socket, setSocket] = useState<WebSocket | null>(null);
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
    const [connected, setConnected] = useState(false);

    // Connect to WebSocket when URL is provided
    useEffect(() => {
        if (!url) {
            if (socket) {
                socket.close();
                setSocket(null);
                setConnected(false);
            }
            return;
        }

        const ws = new WebSocket(url);

        ws.onopen = () => {
            console.log('WebSocket connected');
            setConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setLastMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setConnected(false);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setConnected(false);
        };

        setSocket(ws);

        // Cleanup function
        return () => {
            ws.close();
        };
    }, [url]);

    const sendMessage = useCallback((message: string) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ message }));
        } else {
            console.warn('WebSocket is not connected');
        }
    }, [socket]);

    return {
        sendMessage,
        lastMessage,
        connected
    };
} 