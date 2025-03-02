from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import asyncio

app = FastAPI()

messages = []
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
        print(f"Новое сообщение от {msg.username}: {msg.text}. Отправляем ожидающим клиентам...")

        to_remove = []
        for username, future in waiting_clients.items():
            if username != msg.username and not future.done():
                print(f"Попытка отправить сообщение клиенту {username}")
                print(f"Очередь перед отправкой: {[u for u in waiting_clients]}")
                future.set_result([msg])
                print(f"Отправляем сообщение клиенту {username}!")
                to_remove.append(username)

        for username in to_remove:
            waiting_clients.pop(username, None)

        print(f"Очередь после удаления клиентов: {[u for u in waiting_clients]}")

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    """ Клиент ждёт новые сообщения, если их нет. """
    print(f"Получен запрос от клиента {username} на получение сообщений.")
    
    async with lock:
        pending_messages = [msg for msg in messages if msg.username != username]
        
        if pending_messages:
            print(f"Клиент {username} подключился, сразу отправляем ему {len(pending_messages)} сообщений.")
            messages[:] = [msg for msg in messages if msg.username == username]
            return pending_messages

        future = asyncio.get_event_loop().create_future()
        waiting_clients[username] = future

    try:
        print(f"Клиент {username} ожидает сообщение...")
        new_messages = await future
        print(f"Отправляем сообщение клиенту {username}!!!")
        return new_messages
    finally:
        async with lock:
            waiting_clients.pop(username, None)
            print(f"Клиент {username} удалён из очереди.")

        await cleanup_messages()

async def cleanup_messages():
    async with lock:
        if not waiting_clients:
            print("Все сообщения отправлены всем клиентам, очищаем очередь сообщений...")
            messages.clear()
