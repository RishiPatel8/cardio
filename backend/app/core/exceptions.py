from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError

class AuthError(Exception):
    def __init__(self, message: str, error_code: str = "AUTH_FAILED"):
        self.message = message
        self.error_code = error_code

class NotFoundError(Exception):
    def __init__(self, message: str, error_code: str = "NOT_FOUND"):
        self.message = message
        self.error_code = error_code

async def auth_error_handler(request: Request, exc: AuthError):
    import traceback; traceback.print_exc(); import traceback; traceback.print_exc(); return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message, "error_code": exc.error_code}
    )

async def not_found_error_handler(request: Request, exc: NotFoundError):
    import traceback; traceback.print_exc(); import traceback; traceback.print_exc(); return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "error_code": exc.error_code}
    )

async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    detail = errors[0].get("msg") if errors else "Validation failed"
    import traceback; traceback.print_exc(); import traceback; traceback.print_exc(); return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail, "error_code": "VALIDATION_FAILED", "fields": errors}
    )

async def db_error_handler(request: Request, exc: SQLAlchemyError):
    import traceback; traceback.print_exc(); import traceback; traceback.print_exc(); return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database transaction failure.", "error_code": "DATABASE_ERROR"}
    )

async def jwt_error_handler(request: Request, exc: JWTError):
    import traceback; traceback.print_exc(); import traceback; traceback.print_exc(); return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Cryptographic session token expired or invalid.", "error_code": "TOKEN_INVALID"}
    )
