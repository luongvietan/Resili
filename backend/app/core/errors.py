from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional


class ResiliError(Exception):
    """Base exception for all Resili custom errors."""
    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"
    message: str = "An unexpected error occurred"
    hint: str = "Please try again or contact support"
    docs_url: str = "https://docs.resili.io/errors/internal-server-error"

    def __init__(self, message: Optional[str] = None, hint: Optional[str] = None):
        self.message = message or self.__class__.message
        self.hint = hint or self.__class__.hint

    def to_dict(self) -> dict:
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "hint": self.hint,
                "docs_url": self.docs_url,
            }
        }


class NotFoundError(ResiliError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "The requested resource was not found"
    hint = "Check the resource ID or URL"
    docs_url = "https://docs.resili.io/errors/not-found"


class UnauthorizedError(ResiliError):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Authentication required"
    hint = "Add Authorization: Bearer <key> header"
    docs_url = "https://docs.resili.io/errors/unauthorized"


class ForbiddenError(ResiliError):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action"
    hint = "Check your account permissions or upgrade tier"
    docs_url = "https://docs.resili.io/errors/forbidden"


class SSRFBlockedError(ResiliError):
    status_code = 400
    error_code = "SSRF_BLOCKED"
    message = "The target URL is blocked for security reasons"
    hint = "Only public URLs are allowed. Private IPs and localhost are blocked"
    docs_url = "https://docs.resili.io/errors/ssrf-blocked"


class CreditsExhaustedError(ResiliError):
    status_code = 429
    error_code = "CREDITS_EXHAUSTED"
    message = "Your credits for this month are exhausted"
    hint = "Upgrade to Pro or wait for your credits to reset"
    docs_url = "https://docs.resili.io/errors/credits-exhausted"


# — Exception Handlers —

def _error_response(exc: ResiliError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def resili_error_handler(request: Request, exc: ResiliError) -> JSONResponse:
    return _error_response(exc)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "hint": str(exc.errors()),
                "docs_url": "https://docs.resili.io/errors/validation-error",
            }
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    if not isinstance(detail, str):
        detail = str(detail)
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": detail,
                "hint": "See HTTP status code for context",
                "docs_url": "https://docs.resili.io/errors",
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "hint": "Please try again or contact support",
                "docs_url": "https://docs.resili.io/errors/internal-server-error",
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers — call in app factory."""
    app.add_exception_handler(ResiliError, resili_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
