# Backend Documentation

## Overview
The backend is built using FastAPI, a modern Python web framework that provides high performance and automatic API documentation. It handles resume tailoring, job scraping, and real-time communication with the frontend.

## Architecture
- **FastAPI Application**: Main web server
- **WebSocket Server**: Handles real-time communication
- **Job Scraper Service**: Extracts job details from URLs
- **Resume Tailoring Service**: AI-powered resume customization
- **Database**: PostgreSQL for data persistence

## API Endpoints

### Authentication
```
POST /auth/login
- Description: Authenticate user and get JWT token
- Request Body: { "username": string, "password": string }
- Response: { "access_token": string, "token_type": "bearer" }

POST /auth/register
- Description: Register new user
- Request Body: { "username": string, "email": string, "password": string }
- Response: { "id": string, "username": string, "email": string }
```

### Tailoring Sessions
```
POST /tailoring-sessions/
- Description: Create new tailoring session
- Request Body: FormData with "resume" (PDF file) and "job_url" (string)
- Response: { "id": string, "status": string }

GET /tailoring-sessions/{session_id}
- Description: Get session status and details
- Response: { "id": string, "status": string, "progress": number }

POST /tailoring-sessions/{session_id}/stop
- Description: Stop ongoing tailoring process
- Response: { "status": "stopped" }

POST /tailoring-sessions/{session_id}/chat
- Description: Send message in tailoring session
- Request Body: { "message": string, "context": string }
- Response: WebSocket message
```

### WebSocket Endpoints
```
WS /ws/tailoring/{session_id}
- Description: WebSocket connection for real-time updates
- Message Types:
  - human_input_required: { "type": "human_input_required", "question": string }
  - progress_update: { "type": "progress_update", "message": string }
  - resume_update: { "type": "resume_update", "content": string }
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Tailoring Sessions Table
```sql
CREATE TABLE tailoring_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    status VARCHAR(20) NOT NULL,
    resume_path VARCHAR(255),
    job_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Error Handling
The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

Custom error responses follow this format:
```json
{
    "detail": {
        "message": "Error description",
        "code": "ERROR_CODE"
    }
}
```

## Dependencies
- fastapi
- uvicorn
- python-multipart
- python-jose[cryptography]
- passlib[bcrypt]
- sqlalchemy
- psycopg2-binary
- aiofiles
- beautifulsoup4
- requests
- websockets 