"""Domain exceptions mapped to HTTP responses in the API layer."""

from __future__ import annotations


class AppError(Exception):
    """Base application error with an HTTP status and stable code."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "app_error",
        status_code: int = 400,
        details: dict | list | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Not authenticated", *, code: str = "unauthorized") -> None:
        super().__init__(message, code=code, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", *, code: str = "forbidden") -> None:
        super().__init__(message, code=code, status_code=403)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found", *, code: str = "not_found") -> None:
        super().__init__(message, code=code, status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", *, code: str = "conflict") -> None:
        super().__init__(message, code=code, status_code=409)


class RateLimitError(AppError):
    def __init__(self, message: str = "Too many requests", *, code: str = "rate_limited") -> None:
        super().__init__(message, code=code, status_code=429)
