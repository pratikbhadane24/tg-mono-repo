"""
Health check endpoints for the Telegram service.
"""

from fastapi import APIRouter

from app.models import StandardResponse

router = APIRouter()


@router.get("/health", response_model=StandardResponse[dict[str, str]])
def health():
    """
    Health check endpoint for Telegram service.

    Returns the service health status. Used by load balancers
    and monitoring systems to verify the service is running.

    Returns:
        StandardResponse: Status information with "status": "UP"
    """
    return StandardResponse.success_response(
        message="Service is healthy", data={"status": "UP", "service": "telegram"}
    )


@router.get("/", response_model=StandardResponse[dict[str, str]])
def root():
    """
    Root endpoint providing service information.

    Returns:
        StandardResponse: Service name and version information
    """
    return StandardResponse.success_response(
        message="Telegram Service API",
        data={
            "service": "Telegram Service",
            "version": "1.0.0",
            "description": "Standalone Telegram bot service for channel access management",
            "docs": "/docs",
        },
    )
