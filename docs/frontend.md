# Frontend Documentation

## Overview
The frontend is a React application built with TypeScript and Material-UI. It provides a user-friendly interface for resume tailoring, real-time chat interaction, and markdown preview functionality.

## Architecture
The application follows a component-based architecture with the following structure:

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── hooks/          # Custom React hooks
│   ├── services/       # API and WebSocket services
│   ├── theme/          # Material-UI theme configuration
│   ├── types/          # TypeScript type definitions
│   └── App.tsx         # Main application component
```

## Components

### App Component (`App.tsx`)
The main application component that:
- Manages the overall layout with a split view
- Handles file uploads and job URL input
- Manages WebSocket connections
- Coordinates communication between components

### UploadDialog Component (`components/UploadDialog.tsx`)
Modal dialog for uploading resumes and job details:
- PDF file upload functionality
- Job URL input field
- Input validation
- Error handling

### ChatPanel Component (`components/ChatPanel.tsx`)
Real-time chat interface that:
- Displays conversation history
- Handles user input
- Shows typing indicators
- Manages message timestamps

### MarkdownPreview Component (`components/MarkdownPreview.tsx`)
Resume preview component with:
- Markdown rendering
- Syntax highlighting
- Responsive layout
- Print-friendly styling

## Custom Hooks

### useWebSocket (`hooks/useWebSocket.ts`)
WebSocket management hook that provides:
```typescript
interface WebSocketHook {
  connect: (url: string) => void;
  disconnect: () => void;
  sendMessage: (message: string) => void;
  lastMessage: WebSocketMessage | null;
  connected: boolean;
}
```

## Services

### API Service (`services/api.ts`)
Axios-based HTTP client with:
- Base configuration
- Request/response interceptors
- Error handling
- Authentication token management

## Theme Configuration (`theme/theme.ts`)
Material-UI theme customization:
- Color palette
- Typography
- Component style overrides
- Responsive breakpoints

## State Management
The application uses React's built-in state management with:
- Local component state (useState)
- Side effects (useEffect)
- Memoization (useMemo, useCallback)
- Context API for global state

## WebSocket Communication
Real-time updates are handled through WebSocket connections:

```typescript
interface WebSocketMessage {
  type: 'human_input_required' | 'progress_update' | 'resume_update';
  question?: string;
  message?: string;
  content?: string;
}
```

## Error Handling
The application implements comprehensive error handling:
- API request errors
- WebSocket connection issues
- File upload validation
- Input validation
- Network connectivity problems

## Dependencies
```json
{
  "dependencies": {
    "@emotion/react": "^11.11.3",
    "@emotion/styled": "^11.11.0",
    "@mui/icons-material": "^5.15.11",
    "@mui/material": "^5.15.11",
    "axios": "^1.6.7",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-markdown": "^9.0.1",
    "react-syntax-highlighter": "^15.5.0",
    "typescript": "^5.3.3"
  }
}
```

## Build and Development
- Development server: `npm run dev`
- Production build: `npm run build`
- Type checking: `npm run type-check`
- Linting: `npm run lint`

## Browser Support
The application supports:
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions) 