from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from routers import users, notes, admins, accesses, errors_handler
from database.general import init_db

app = FastAPI()
app.include_router(admins.router)
app.include_router(users.router)
app.include_router(notes.router)
app.include_router(accesses.router)
app.add_exception_handler(RequestValidationError, errors_handler.validation_exception_handler)


if __name__ == "__main__":
    init_db()

    import uvicorn
    uvicorn.run(app="main:app", host="127.0.0.1", port=80, reload=True)
