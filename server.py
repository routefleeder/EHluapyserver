from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

active_clients = {}
active_sender: WebSocket | None = None
message_sent = False


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global active_clients, active_sender, message_sent

    try:
        await websocket.accept()
        active_clients[id(websocket)] = websocket
        print(f"New client connected: {websocket}")
        print("\n", list(active_clients.keys()), "\n")
        for client_id, client in list(active_clients.items()):
            print("\n", list(active_clients.keys()), "\n")
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
                    
                    for client_id, client in list(active_clients.items()):
                        print("\n", list(active_clients.keys()), "\n")
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

                for client_id, client in list(active_clients.items()):
                    print("\n", list(active_clients.keys()), "\n")
                    await client.send_text(message)

            else:
                await websocket.send_text("deactivate_first")

    except WebSocketDisconnect:
        active_clients.pop(id(websocket), None)
        if active_sender == websocket:
            active_sender = None
            message_sent = False
            for client_id, client in list(active_clients.items()):
                try:
                    print("\n", list(active_clients.keys()), "\n")
                    await client.send_text("player_discon")
                except:
                    pass
        print(f"Клиент отключился: {websocket}")
