from fastapi import FastAPI
import uvicorn

app = FastAPI()  # Create an instance of FastAPI

@app.get("/")  # Define a base endpoint
async def read_root():
    return {"message": "hello"}  

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # Replace 'main:app' with the module and app instance of your FastAPI app
        host="127.0.0.1",
        port=8000,
        reload=True  # Enable auto-reload for development
    )