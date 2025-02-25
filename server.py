from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/api/notify")
def notify():
    print("Получена команда /arpem")
    return {"status": "Message received"}
