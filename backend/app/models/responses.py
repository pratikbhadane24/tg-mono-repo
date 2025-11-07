"""
Standardized API response models.

All API endpoints should return responses conforming to these models
for consistent, predictable API responses.
"""

from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail model."""

    code: str = Field(..., description="Error code")
    description: str = Field(..., description="Error description")


class StandardResponse[T](BaseModel):
    """
    Standard API response format.

    All API endpoints should return this format for consistency.

    Fields:
        success: Whether the request was successful
        message: Human-readable message
        data: Response data (type varies by endpoint)
        error: Error details if success is False
    """

    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message")
    data: T | None = Field(default=None, description="Response data")
    error: ErrorDetail | None = Field(default=None, description="Error details if unsuccessful")

    @classmethod
    def success_response(cls, message: str, data: T | None = None) -> "StandardResponse[T]":
        """Create a successful response."""
        return cls(success=True, message=message, data=data, error=None)

    @classmethod
    def error_response(
        cls, message: str, error_code: str, error_description: str
    ) -> "StandardResponse[T]":
        """Create an error response."""
        return cls(
            success=False,
            message=message,
            data=None,
            error=ErrorDetail(code=error_code, description=error_description),
        )
