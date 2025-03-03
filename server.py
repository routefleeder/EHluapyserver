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
                    if active_sender is None:
                        await websocket.send_text("no_active_event")
                    pass
                continue

            if active_sender == websocket:
                await websocket.send_text("deactivate_first")
                continue

            print(f"Checking active_sender: {active_sender}")
            if active_sender is not None and active_sender != websocket:
                print(f"Waiting for deactivation. Sending 'wait_for_deactivation' to {websocket}")
                await websocket.send_text("wait_for_deactivation")
                continue

            if not message_sent:
                active_sender = websocket
                message_sent = True
                print(f"Setting active_sender to {websocket}")

                disconnected_clients = []
                for client in active_clients:
                    try:
                        await client.send_text(message)
                    except Exception as e:
                        print(f"Error sending message to {client}: {e}")
                        disconnected_clients.append(client)

                for client in disconnected_clients:
                    active_clients.discard(client)
            else:
                await websocket.send_text("deactivate_first")

    except WebSocketDisconnect:
        active_clients.discard(websocket)
        if active_sender == websocket:
            active_sender = None
            message_sent = False
            for client in active_clients:
                await client.send_text("player_discon")
        print(f"Клиент отключился: {websocket}")
