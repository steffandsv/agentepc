from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import json
import logging
from typing import List

from app.agent_service import AgentService, TaskRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FastAPI")

app = FastAPI(title="Browser Agent Control Panel")

# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                # Potentially remove dead connection
                pass

manager = ConnectionManager()
agent_service = AgentService.get_instance()

# Link AgentService to WebSocket Manager
async def agent_callback(data: dict):
    await manager.broadcast(data)

agent_service.add_subscriber(agent_callback)

@app.get("/")
async def read_index():
    return FileResponse("app/static/index.html")

@app.post("/api/start")
async def start_task(request: TaskRequest):
    return await agent_service.start_task(request.task)

@app.post("/api/stop")
async def stop_task():
    return await agent_service.stop_task()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive / listen for client messages if needed
            data = await websocket.receive_text()
            # We can handle commands from WS too if we want
    except WebSocketDisconnect:
        manager.disconnect(websocket)
