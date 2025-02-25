from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/api/notify")
async def notify():
    print("Получена команда /arpem")
    return {"status": "Message received"}
