from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .websockets.connection_manager import connection_manager
from src.utils.logger_config import setup_logger

logger = setup_logger(__name__)

app = FastAPI(title="Resume Tailoring")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    try:
        logger.info(f"WebSocket connection request for session {session_id}")
        await connection_manager.connect(session_id, websocket)
        
        # Keep the connection alive until client disconnects
        while True:
            # Wait for any message from the client (just to detect disconnection)
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        connection_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        connection_manager.disconnect(session_id)
