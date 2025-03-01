from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import asyncio

app = FastAPI()

waiting_clients = []
lock = asyncio.Lock()

class ChatMessage(BaseModel):
    username: str
    playerid: int
    text: str

@app.post("/api/notify")
async def send_message(msg: ChatMessage):
    async with lock:
        if waiting_clients:
            print(f"Новое сообщение от {msg.username}: {msg.text}. Отправляем ожидающим клиентам...")
            for username, client_queue in waiting_clients[:]:
                if username != msg.username:
                    await client_queue.put([msg])

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    """ Клиент ждёт новые сообщения. Сервер не отвечает сразу, если их нет. """
    my_queue = asyncio.Queue()
    async with lock:
        waiting_clients.append((username, my_queue))

    try:
        print(f"Клиент {username} ожидает сообщение...")
        new_messages = await my_queue.get()
        print(f"Отправляем сообщение клиенту {username}!")
        return new_messages
    finally:
        async with lock:
            waiting_clients[:] = [(u, q) for u, q in waiting_clients if q != my_queue]
            print(f"Клиент {username} удалён из очереди.")
