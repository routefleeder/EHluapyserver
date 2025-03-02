from fastapi import FastAPI
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
        print(f"Новое сообщение от {msg.username}: {msg.text}. Рассылаем ожидающим клиентам...")

        # Сообщение отправляется всем, кто его ждал
        to_remove = []
        for username, future in waiting_clients.items():
            if username != msg.username and not future.done():
                print(f"Отправляем сообщение клиенту {username}")
                # Отправляем все сообщения, которые могут быть
                future.set_result([msg])
                to_remove.append(username)

        # Удаляем из очереди клиентов, получивших свои сообщения
        for username in to_remove:
            waiting_clients.pop(username, None)

        print(f"Текущая очередь ожидания: {list(waiting_clients.keys())}")

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    print(f"Получен запрос от клиента {username} на получение сообщений.")

    async with lock:
        # Выбираем все сообщения, кроме тех, что были отправлены этому клиенту
        pending_messages = [msg for msg in messages if msg.username != username]

        # Если есть сообщения, отправляем их сразу
        if pending_messages:
            print(f"Клиент {username} сразу получает {len(pending_messages)} сообщений.")
            return pending_messages

        # Если сообщений нет, то создаём будущий объект, в котором будем ждать сообщения
        future = asyncio.get_event_loop().create_future()
        waiting_clients[username] = future

    try:
        print(f"Клиент {username} ждёт новые сообщения...")
        # Когда сообщение появится, оно будет отправлено клиенту
        return await future
    finally:
        async with lock:
            # После того как клиент получит свои сообщения, удаляем его из очереди
            waiting_clients.pop(username, None)
            print(f"Клиент {username} удалён из очереди ожидания.")
