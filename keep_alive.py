from fastapi import FastAPI
import threading
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "alive"}

def run():
    uvicorn.run(app, host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()