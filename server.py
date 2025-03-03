from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

active_clients = set()
active_sender = None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_clients.add(websocket)

    try:
        while True:
            message = await websocket.receive_text()

            if message is not None and message != '':

                active_sender = websocket
    
                if message == "deactivate":
                    if active_sender == websocket:
                        active_sender = None
                        await websocket.send_text("deactivated")
                    continue
    
                if active_sender and active_sender != websocket:
                    await websocket.send_text("wait_for_deactivation")
                    continue
    
                for client in active_clients:
                    await client.send_text(message)

    except WebSocketDisconnect:
        active_clients.discard(websocket)
        if active_sender == websocket:
            active_sender = None
        print(f"Клиент отключился")
