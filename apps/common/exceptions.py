"""
apps/common/exceptions.py

Custom DRF exception handler that returns consistent error shapes:

{
  "status": "error",
  "code": 400,
  "message": "Validation failed",
  "errors": { "field": ["msg"] }
}
"""

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


def erp_exception_handler(exc, context):
    # Let DRF handle its own exceptions first
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "status": "error",
            "code": response.status_code,
            "message": _get_message(response.data),
            "errors": response.data if isinstance(response.data, dict) else {"detail": response.data},
        }
        return response

    # Handle Django core exceptions not caught by DRF
    if isinstance(exc, DjangoValidationError):
        return Response(
            {
                "status": "error",
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error.",
                "errors": {"detail": exc.messages},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {
                "status": "error",
                "code": status.HTTP_403_FORBIDDEN,
                "message": "Permission denied.",
                "errors": {},
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    return None


def _get_message(data):
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        if "non_field_errors" in data:
            return str(data["non_field_errors"][0])
    if isinstance(data, list) and data:
        return str(data[0])
    return "An error occurred."
