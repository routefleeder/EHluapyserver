from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import asyncio

app = FastAPI()

class ChatMessage(BaseModel):
    username: str
    playerid: int
    text: str

messages: List[ChatMessage] = []
waiting_clients: Dict[str, asyncio.Future] = {}
lock = asyncio.Lock()

@app.post("/api/notify")
async def send_message(msg: ChatMessage):
    async with lock:
        messages.append(msg)
        print(f"Новое сообщение от {msg.username}: {msg.text}. Рассылаем клиентам...")
        
        to_remove = []
        for username, future in waiting_clients.items():
            if username != msg.username and not future.done():
                future.set_result(messages.copy())  # Отправляем все сообщения сразу
                to_remove.append(username)

        for username in to_remove:
            waiting_clients.pop(username, None)

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    async with lock:
        pending_messages = [msg for msg in messages if msg.username != username]
        if pending_messages:
            return pending_messages
        
        future = asyncio.get_event_loop().create_future()
        waiting_clients[username] = future
    
    try:
        return await future
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        async with lock:
            waiting_clients.pop(username, None)
