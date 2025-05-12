from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
import uvicorn
from routers import users

app = FastAPI()  # Create an instance of FastAPI

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow requests from your frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(users.router)  # Include the users router

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