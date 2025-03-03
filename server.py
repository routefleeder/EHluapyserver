from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

active_clients = set()
active_sender = None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global active_sender
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
                    await websocket.send_text("deactivated")
                    print(f"Active sender {websocket} deactivated")
                else:
                    await websocket.send_text("no_active_event")
                continue

            print(f"Checking active_sender: {active_sender}")
            if active_sender is not None and active_sender != websocket:
                print(f"Waiting for deactivation. Sending 'wait_for_deactivation' to {websocket}")
                await websocket.send_text("wait_for_deactivation")
                print("Sent 'wait_for_deactivation' to ", websocket)
                continue

            if active_sender is None:
                active_sender = websocket
                print(f"Setting active_sender to {websocket}")

            for client in active_clients:
                await client.send_text(message)

    except WebSocketDisconnect:
        active_clients.discard(websocket)
        if active_sender == websocket:
            active_sender = None
            for client in active_clients:
                await client.send_text("player_discon")
        print(f"Клиент отключился: {websocket}")
