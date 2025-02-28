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
            client = waiting_clients.pop(0)
            await client.put([msg])

    return {"status": "ok"}

@app.get("/api/notify", response_model=List[ChatMessage])
async def get_messages(username: str):
    """ Клиент ждёт новые сообщения. Сервер не отвечает сразу, если их нет. """
    my_queue = asyncio.Queue()
    waiting_clients.append((username, my_queue))

    try:
        messages = await my_queue.get()
        return [msg for msg in messages if msg.username != username]
    except asyncio.CancelledError:
        waiting_clients.remove((username, my_queue))
