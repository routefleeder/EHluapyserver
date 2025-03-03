from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

active_clients = set()
active_sender: WebSocket | None = None
message_sent = False


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global active_sender, message_sent
    await websocket.accept()
    active_clients.add(websocket)
    print(f"New client connected: {websocket}")

    try:
        while True:
            message = await websocket.receive_text()

            if not message:
                continue

            print(f"Received message from {websocket}: {message}")

            if message == "deactivate":
                if active_sender == websocket:
                    active_sender = None
                    message_sent = False
                    await websocket.send_text("deactivated")
                    print(f"Active sender {websocket} deactivated")
                else:
                    await websocket.send_text("no_active_event")
                continue

            if active_sender == websocket:
                await websocket.send_text("deactivate_first")
                continue

            # Если есть активный отправитель, но он не тот же, кто послал запрос
            if active_sender is not None and active_sender != websocket:
                await websocket.send_text("wait_for_deactivation")
                continue

            # Разрешаем только если еще не было сообщения
            if not message_sent:
                active_sender = websocket
                message_sent = True
                print(f"Setting active_sender to {websocket}")

                disconnected_clients = []
                # Создаем копию списка, чтобы избежать изменений во время итерации
                for client in list(active_clients):
                    try:
                        await client.send_text(message)
                    except Exception as e:
                        print(f"Error sending message to {client}: {e}")
                        disconnected_clients.append(client)

                # Удаляем отключившихся клиентов
                for client in disconnected_clients:
                    active_clients.discard(client)

            else:
                await websocket.send_text("deactivate_first")

    except WebSocketDisconnect:
        active_clients.discard(websocket)
        if active_sender == websocket:
            active_sender = None
            message_sent = False  # Сбрасываем флаг, чтобы следующий клиент мог отправить сообщение
            for client in list(active_clients):
                try:
                    await client.send_text("player_discon")
                except:
                    pass
        print(f"Клиент отключился: {websocket}")
