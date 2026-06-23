from fastapi import Request, status
from fastapi.responses import JSONResponse

class AdherenceException(Exception):
    def __init__(self, message: str):
        self.message = message

async def adherence_exception_handler(request: Request, exc: AdherenceException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message},
    )
