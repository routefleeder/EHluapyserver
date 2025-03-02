from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import asyncio

app = FastAPI()

messages: List[ChatMessage] = []
waiting_clients: Dict[str, asyncio.Future] = {}
lock = asyncio.Lock()

class ChatMessage(BaseModel):
    username: str
    playerid: int
    text: str

@app.post("/api/notify")
async def send_message(msg: ChatMessage):
    async with lock:
        messages.append(msg)
        print(f"Новое сообщение от {msg.username}: {msg.text}. Рассылаем ожидающим клиентам...")

        to_remove = []
        for username, future in waiting_clients.items():
            if username != msg.username and not future.done():
                print(f"Отправляем сообщение клиенту {username}")
                future.set_result([msg])
                to_remove.append(username)

        for username in to_remove:
            waiting_clients.pop(username, None)

        print(f"Текущая очередь ожидания: {list(waiting_clients.keys())}")

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    print(f"Получен запрос от клиента {username} на получение сообщений.")

    async with lock:
        pending_messages = [msg for msg in messages if msg.username != username]

        if pending_messages:
            print(f"Клиент {username} сразу получает {len(pending_messages)} сообщений.")
            return pending_messages

        future = asyncio.get_event_loop().create_future()
        waiting_clients[username] = future

    try:
        print(f"Клиент {username} ждёт новые сообщения...")
        return await future
    finally:
        async with lock:
            waiting_clients.pop(username, None)
            print(f"Клиент {username} удалён из очереди ожидания.")
