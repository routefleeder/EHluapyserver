from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# Список подключенных клиентов
active_clients = []


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_clients.append(websocket)

    try:
        while True:
            # Ждем строку от клиента
            message = await websocket.receive_text()

            # Рассылаем её всем подключенным клиентам
            for client in active_clients:
                await client.send_text(message)

    except WebSocketDisconnect:
        active_clients.remove(websocket)
        print(f"Клиент отключился")
