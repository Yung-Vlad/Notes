from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from typing import AsyncContextManager
from contextlib import asynccontextmanager
from routers import users, notes, admins, accesses, errors_handler
from database.general import init_db
from database.notes import check_active_time


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncContextManager[None]:
    # Startup
    await check_active_time()

    yield

    # Shutdown


app = FastAPI(lifespan=lifespan)

app.include_router(admins.router)
app.include_router(users.router)
app.include_router(notes.router)
app.include_router(accesses.router)

app.add_exception_handler(RequestValidationError, errors_handler.validation_exception_handler)


if __name__ == "__main__":
    init_db()

    import uvicorn
    uvicorn.run(app="main:app", host="127.0.0.1", port=80, reload=True)
