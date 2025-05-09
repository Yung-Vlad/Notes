from fastapi import FastAPI

from routers import users, notes, admins, accesses
from database.general import init_db


app = FastAPI()
app.include_router(admins.router)
app.include_router(users.router)
app.include_router(notes.router)
app.include_router(accesses.router)

if __name__ == "__main__":
    init_db()

    import uvicorn
    uvicorn.run(app="main:app", host="127.0.0.1", port=80, reload=True)
