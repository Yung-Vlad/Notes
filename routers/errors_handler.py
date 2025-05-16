from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import ValidationException
from fastapi.encoders import jsonable_encoder


async def validation_exception_handler(request: Request, exc: Exception | ValidationException) -> Response:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message":  "Validation error",
            "details": jsonable_encoder(
                [
                    {
                        "field": error["loc"][1],
                        "message": error["msg"],
                        "input": error["input"],
                        "context": error["ctx"]
                    } for error in exc.errors()
                ]
            )
        }
    )
