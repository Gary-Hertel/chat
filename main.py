import asyncio

from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect


app = FastAPI()


class RoomManager:
    """Chat Rooms Manager."""

    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, room_name: str):
        """Add a user into specific chat room."""
        await websocket.accept()
        connection_list: list = self.rooms.get(room_name, [])
        connection_list.append(websocket)
        self.rooms[room_name] = connection_list

    async def disconnect(self, websocket: WebSocket, room_name: str):
        """Remove a user from specific chat room."""
        connection_list: list = self.rooms.get(room_name, [])
        connection_list.remove(websocket)
        if not connection_list:
            self.rooms.pop(room_name)
        
    async def broadcast_message(self, room_name: str, message: dict, speaker: WebSocket):
        """Broadcast message to specific chat room."""
        connection_list = self.rooms.get(room_name, [])
        for connection in connection_list:
            if connection is speaker:
                continue
            await connection.send_json(message)
        

room_manager = RoomManager()


@app.websocket("/{room_name}")
async def websocket_endpoint(websocket: WebSocket, room_name: str):
    
    username = ""
    await room_manager.connect(websocket, room_name)
    
    try:
        
        while True:
            await asyncio.sleep(0.1)
            data: dict = await websocket.receive_json()
            if not username:
                username = data.get("username")
                data.update(status="join")
            else:
                data.update(status="speak")
            await room_manager.broadcast_message(room_name, data, websocket)

    except WebSocketDisconnect:
        await room_manager.disconnect(websocket, room_name)
        await room_manager.broadcast_message(room_name, {"username": username, "text": f"{username} has left", "status": "left"}, websocket)


if __name__ == "__main__":
    
    import uvicorn
    msg = {"username": "smith", "text": "do not go gentle to that good night", "status": "speak"}
    uvicorn.run(app='main:app', host="0.0.0.0", port=8080, reload=True, debug=True)