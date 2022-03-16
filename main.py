import asyncio
import requests

from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware  # 引入 CORS 中间件模块


app = FastAPI()


# 设置跨域传参
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 设置允许的origins来源
    allow_credentials=True,
    allow_methods=["*"],  # 设置允许跨域的http方法，比如 get、post、put等。
    allow_headers=["*"])  # 允许跨域的headers，可以用来鉴别来源等作用。


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


@app.get("/random_name")
def get_random_name():
    url = "https://api.iyk0.com/sjxm"
    response = requests.get(url).json()
    name = response.get("name")
    return {"data": name}


@app.get("/random_avatar")
def get_random_avatar():
    url = "https://api.iyk0.com/sjtx/?msg=%E5%A5%B3"
    response = requests.get(url).json()
    img = response.get("img")
    return {"data": img}


@app.websocket("/{room_name}")
async def websocket_endpoint(websocket: WebSocket, room_name: str):
    
    await room_manager.connect(websocket, room_name)
    data: dict = await websocket.receive_json()
    username = data.get("username")
    await room_manager.broadcast_message(
        room_name,
        {"username": username, "text": f"{username} join", "status": "join"},
        websocket
    )
    
    try:
        while True:
            await asyncio.sleep(0.1)
            data: dict = await websocket.receive_json()
            await room_manager.broadcast_message(room_name, data, websocket)

    except WebSocketDisconnect:
        await room_manager.disconnect(websocket, room_name)
        await room_manager.broadcast_message(room_name, {"username": username, "text": f"{username} left", "status": "left"}, websocket)


if __name__ == "__main__":
    
    import uvicorn
    
    uvicorn.run(app='main:app', host="0.0.0.0", port=8501, reload=True, debug=True)