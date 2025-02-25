from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/api/notify")
def notify():
    print("Получена команда /arpem")
    return {"status": "Message received"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
