from __future__ import annotations

import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ProblemDetails(BaseModel):
    """RFC 9457 problem details. `traceId` is the sole camelCase member,
    required verbatim by the framework's API contract validator."""

    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    code: str
    traceId: str


class BrainError(Exception):
    """Base class for domain/application errors mapped to ProblemDetails."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    title: str = "Internal Server Error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.title)
        self.detail = detail


class NotFoundError(BrainError):
    """Resource absent or access denied — indistinguishable to the caller (F0001-S0006
    logic flow step 5: denied reads are reported as 404, never 403)."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    title = "Not Found"


class UnprocessableError(BrainError):
    """Event cannot be mapped to a review item or reviewer principal."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "unprocessable"
    title = "Unprocessable"


class InvalidRangeApiError(BrainError):
    """Empty or null `valid` range on a commit proposal (F0001-S0005)."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "invalid_range"
    title = "Invalid Range"


class StaleVersionApiError(BrainError):
    """`expected_current_version_id` no longer matches the slot's current
    version(s) — the optimistic-concurrency half of F0001-S0005."""

    status_code = status.HTTP_409_CONFLICT
    code = "stale_version"
    title = "Stale Version"


class ConcurrentCommitApiError(BrainError):
    """The database-level GiST exclusion constraint fired — a concurrent commit
    on the same slot won the race after the row lock was released."""

    status_code = status.HTTP_409_CONFLICT
    code = "concurrent_commit"
    title = "Concurrent Commit"


def _problem_response(
    *,
    status_code: int,
    title: str,
    code: str,
    detail: str | None,
    instance: str | None,
) -> JSONResponse:
    problem = ProblemDetails(
        type="about:blank",
        title=title,
        status=status_code,
        detail=detail,
        instance=instance,
        code=code,
        traceId=str(uuid.uuid4()),
    )
    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(mode="json"),
        media_type="application/problem+json",
    )


def install_problem_details_handlers(app: FastAPI) -> None:
    """Map BrainError subclasses and request-validation failures to ProblemDetails."""

    @app.exception_handler(BrainError)
    async def _handle_brain_error(request: Request, exc: BrainError) -> JSONResponse:
        return _problem_response(
            status_code=exc.status_code,
            title=exc.title,
            code=exc.code,
            detail=exc.detail,
            instance=str(request.url.path),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            title="Request Validation Failed",
            code="validation_error",
            detail=str(exc.errors()),
            instance=str(request.url.path),
        )
