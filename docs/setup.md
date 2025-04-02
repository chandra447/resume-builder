# Setup Guide

## Prerequisites
- Docker and Docker Compose
- Node.js (v18 or later)
- Python (v3.9 or later)
- PostgreSQL (v14 or later)
- Git

## Environment Variables

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/resume_builder
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=resume_builder

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Service
OPENAI_API_KEY=your-openai-api-key
MODEL_NAME=gpt-4-turbo-preview

# Server
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
PROJECT_NAME=Resume Builder
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/resume-builder.git
cd resume-builder
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configurations

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
# Install dependencies
cd frontend
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configurations

# Start development server
npm run dev
```

## Docker Setup

### 1. Build and Run with Docker Compose
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Docker Compose Configuration
```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/resume_builder
    depends_on:
      - db

  db:
    image: postgres:14
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=resume_builder
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Production Deployment

### 1. Security Considerations
- Use strong, unique passwords
- Enable HTTPS
- Set up proper firewalls
- Configure rate limiting
- Implement proper logging

### 2. Environment Configuration
- Use production-grade database
- Set up proper CORS origins
- Configure proper WebSocket URLs
- Use production API keys

### 3. Deployment Steps
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy services
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose exec backend alembic upgrade head
```

## Troubleshooting

### Common Issues

1. **Database Connection**
```bash
# Check database status
docker-compose ps db
# View database logs
docker-compose logs db
```

2. **Backend API**
```bash
# Check backend status
docker-compose ps backend
# View backend logs
docker-compose logs backend
```

3. **Frontend Development**
```bash
# Clear npm cache
npm cache clean --force
# Reinstall dependencies
rm -rf node_modules
npm install
```

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Database health
docker-compose exec db pg_isready

# Frontend build
npm run build
```

## Development Tools

### Code Quality
```bash
# Backend
pytest
flake8
black .
isort .

# Frontend
npm run lint
npm run type-check
npm run test
```

### Database Management
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Monitoring

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Metrics
- Backend metrics: http://localhost:8000/metrics
- Database metrics: PostgreSQL monitoring tools
- Container metrics: Docker stats 