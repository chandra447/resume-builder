import { useState, useCallback, useEffect } from 'react';

interface WebSocketMessage {
    type: 'human_input_required' | 'progress_update' | 'resume_update';
    question?: string;
    message?: string;
    content?: string;
}

export function useWebSocket() {
    const [socket, setSocket] = useState<WebSocket | null>(null);
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
    const [connected, setConnected] = useState(false);

    const connect = useCallback((url: string) => {
        if (socket) {
            socket.close();
        }

        const ws = new WebSocket(url);

        ws.onopen = () => {
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
            setConnected(false);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setConnected(false);
        };

        setSocket(ws);
    }, []);

    const disconnect = useCallback(() => {
        if (socket) {
            socket.close();
            setSocket(null);
            setConnected(false);
        }
    }, [socket]);

    const sendMessage = useCallback((message: string) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ message }));
        }
    }, [socket]);

    useEffect(() => {
        return () => {
            if (socket) {
                socket.close();
            }
        };
    }, [socket]);

    return {
        connect,
        disconnect,
        sendMessage,
        lastMessage,
        connected
    };
} 