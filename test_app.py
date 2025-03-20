from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "App is running!"}

@app.get("/api/test")
async def test():
    return {"status": "API is operational"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 