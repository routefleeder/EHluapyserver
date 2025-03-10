from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

active_clients = set()
active_sender: WebSocket | None = None
message_sent = False


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global active_clients, active_sender, message_sent

    try:
        if websocket not in active_clients:
            await websocket.accept()
            active_clients.add(websocket)
            print(f"New client connected: {websocket}")
            print("\n", list(active_clients), "\n")
            for client in active_clients:
                print("\n", list(active_clients), "\n")
                await client.send_text(f"Online: {len(active_clients)}")
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
                    
                    for client in active_clients:
                        print("\n", list(active_clients), "\n")
                        await client.send_text("emergency_deactivated")
                else:
                    await websocket.send_text("no_active_event")
                continue

            if active_sender == websocket:
                await websocket.send_text("deactivate_first")
                continue

            if active_sender is not None and active_sender != websocket:
                await websocket.send_text("wait_for_deactivation")
                continue

            if not message_sent:
                active_sender = websocket
                message_sent = True
                print(f"Setting active_sender to {websocket}")

                for client in active_clients:
                    print("\n", list(active_clients), "\n")
                    await client.send_text(message)

            else:
                await websocket.send_text("deactivate_first")

    except WebSocketDisconnect:
        if websocket in active_clients:
            active_clients.remove(websocket)
        if active_sender == websocket:
            active_sender = None
            message_sent = False
            for client in active_clients:
                try:
                    print("\n", list(active_clients), "\n")
                    await client.send_text("player_discon")
                    await client.send_text(f"Online: {len(active_clients)}")
                except:
                    pass
        print(f"Клиент отключился: {websocket}")
