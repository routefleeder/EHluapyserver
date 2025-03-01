from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import asyncio

app = FastAPI()

messages = []
waiting_clients = []
lock = asyncio.Lock()

class ChatMessage(BaseModel):
    username: str
    playerid: int
    text: str

@app.post("/api/notify")
async def send_message(msg: ChatMessage):
    async with lock:
        messages.append(msg)
        if waiting_clients:
            print(f"Новое сообщение от {msg.username}: {msg.text}. Отправляем ожидающим клиентам...")
            for username, client_queue in waiting_clients[:]:
                if username != msg.username:
                    await client_queue.put(messages[:])

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    """ Клиент ждёт новые сообщения. Сервер не отвечает сразу, если их нет. """
    # Временные логи
    print(f"Получен запрос от клиента {username} на получение сообщений.")
    #
    my_queue = asyncio.Queue()
    async with lock:
        pending_messages = [msg for msg in messages if msg.username != username]
        if pending_messages:
            print(f"Клиент {username} подключился, сразу отправляем ему {len(pending_messages)} сообщений.")
            return pending_messages
        
        waiting_clients.append((username, my_queue))

    try:
        print(f"Клиент {username} ожидает сообщение...")
        new_messages = await my_queue.get()
        print(f"Отправляем сообщение клиенту {username}!")
        return new_messages
    finally:
        async with lock:
            waiting_clients[:] = [(u, q) for u, q in waiting_clients if u != username]
            print(f"Клиент {username} удалён из очереди.")

        await cleanup_messages()

async def cleanup_messages():
    async with lock:
        all_received = True
        for username in waiting_clients:
            for msg in messages:
                if msg.username != username:
                    all_received = False
                    break
            if not all_received:
                break

        if all_received:
            print("Все сообщения отправлены всем клиентам, очищаем очередь сообщений...")
            messages.clear()
