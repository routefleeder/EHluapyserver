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

        while waiting_clients:
            _, client_queue = waiting_clients.pop(0)
            await client_queue.put([msg])

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    """ Клиент ждёт новые сообщения. Сервер не отвечает сразу, если их нет. """
    my_queue = asyncio.Queue()
    waiting_clients.append((username, my_queue))

    try:
        messages = await my_queue.get()
        return [msg for msg in messages if msg.username != username]
    finally:
        waiting_clients[:] = [(u, q) for u, q in waiting_clients if u != username or q != my_queue]
