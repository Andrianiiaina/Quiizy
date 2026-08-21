from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} '{resource_id}' not found.",
            status_code=404,
        )


class AccessDeniedError(AppException):
    def __init__(self, resource: str = "resource") -> None:
        super().__init__(
            code="ACCESS_DENIED",
            message=f"You do not have permission to access this {resource}.",
            status_code=403,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )
