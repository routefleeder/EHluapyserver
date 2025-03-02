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
client_last_message: Dict[str, int] = {}  # Храним индексы последнего сообщения для каждого клиента
lock = asyncio.Lock()

@app.post("/api/notify")
async def send_message(msg: ChatMessage):
    async with lock:
        messages.append(msg)
        print(f"Новое сообщение от {msg.username}: {msg.text}. Рассылаем клиентам...")

        # Отправляем сообщения всем клиентам, у которых есть незавершенные запросы
        for username, future in list(waiting_clients.items()):
            if username != msg.username and not future.done():
                future.set_result([msg])  # Отправляем только новое сообщение
                del waiting_clients[username]

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    async with lock:
        # Находим, какое сообщение клиент видел последним
        last_msg_index = client_last_message.get(username, -1)

        # Фильтруем только новые сообщения
        new_messages = [msg for idx, msg in enumerate(messages) if idx > last_msg_index and msg.username != username]
        
        if new_messages:
            # Обновляем информацию о последнем полученном сообщении
            client_last_message[username] = len(messages) - 1
            return new_messages

        # Если нет новых сообщений, ждем их
        future = asyncio.get_event_loop().create_future()
        waiting_clients[username] = future

    try:
        return await future
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        async with lock:
            # Убираем клиента из списка ожидания
            waiting_clients.pop(username, None)
