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

        for username, future in list(waiting_clients.items()):
            if username != msg.username and not future.done():
                future.set_result([msg])  # Отправляем только новое сообщение
                del waiting_clients[username]

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    async with lock:
        # Фильтруем сообщения, чтобы не отправлять клиенту его собственные сообщения
        pending_messages = [msg for msg in messages if msg.username != username]
        
        if pending_messages:
            return pending_messages

        # Если нет новых сообщений, ждем их
        future = asyncio.get_event_loop().create_future()
        waiting_clients[username] = future

    try:
        return await future
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Убираем клиента из списка ожидания
        async with lock:
            waiting_clients.pop(username, None)
