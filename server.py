from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import asyncio

app = FastAPI()

messages = []
waiting_clients = []
lock = asyncio.Lock()  # Добавляем блокировку для защиты ресурса

class ChatMessage(BaseModel):
    username: str
    playerid: int
    text: str

@app.post("/api/notify")
async def send_message(msg: ChatMessage):
    async with lock:  # Защищаем доступ к ресурсу
        messages.append(msg)  # Сохраняем сообщение

        # Отправляем сообщение всем ожидающим клиентам
        while waiting_clients:
            client = waiting_clients.pop(0)
            await client.put([msg])

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    """ Клиент ждёт новые сообщения. Сервер не отвечает сразу, если их нет. """
    my_queue = asyncio.Queue()
    waiting_clients.append(my_queue)

    try:
        # Ожидаем сообщение (но не больше 30 секунд)
        return await asyncio.wait_for(my_queue.get(), timeout=30)
    except asyncio.TimeoutError:
        return []
